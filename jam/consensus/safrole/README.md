# Safrole Notes - Block Production and Chain Growth

### **Overview**

JAM has a hybrid consensus system SAFROLE+GRANDPA, where Safrole is used for Block production and GRANDPA for finalization. Safrole is a simplified version of [SASSAFRAS](https://research.web3.foundation/Polkadot/protocols/block-production/SASSAFRAS)

### **State ($\gamma$)**


Safrole state ($\gamma$) is divided into four parts:

1. **$\gamma_\mathbf{k}$**
  
Pending set of validator keys for the next epoch. These will become $\kappa$ and validate blocks for next epoch.

2. **$\gamma_z$**

Ring VRF Root composed of Bandersnatch keys for the **upcoming** epoch's validators ($\gamma_\mathbf{k}$).

3. **$\gamma_\mathbf{a}$**

Tickets are collected here for the next epoch. Sorts them by highest-to-lowest (`id` scalar value) scoring ticket.

4.  **$\gamma_\mathbf{s}$**

Current epoch's sealing key sequence. This is either a set of winning Tickets [C] or in case of any fallback - a set of Bandersnatch public keys [H]. This sequence defines who gets to produce block within this epoch. 


----
Safrole interacts with other state components:
  - **$\iota$**: Staging set of validator keys. Maybe this comes from a list of all available validators (ordered by staked amount / some other parameter).
  - **$\kappa$**: Active set of validator keys.
  - **$\tau$**: Most recent block's timeslot index. Indicating the number of six-second intervals since the Jam Common Era began.
  - **$\eta$**: Entropy accumulator.


### Validator Rotation

At the end of each epoch:

filter($\iota$) > $\gamma_{k}$ > $\kappa$ > $\lambda$

`filter` function on $\iota$ removes offenders, and MIGHT order them based some parameter

---

### **Tickets ($\mathbb{C}$)**

- **Structure**: Each ticket consists of:
  - **Ticket Identifier ($\mathbf{y}$)**: A high-entropy, unbiasable 32-byte sequence.
  - **Entry-Index ($r$)**: An integer representing the validator's attempt (0 or 1)

- **Purpose**: Tickets are used to select validators for block production slots in the upcoming epoch.

### **Seal Signatures**

- **Requirement**: Every block header must include a valid seal signature ($\mathbf{H}_s$), proving that the block was authored by an authorized validator.

---

## 6.3. **Key Rotation**



### **Validator Key Structure ($K$)**

Each validator key $k$ is a 336-byte sequence divided into:
- **Bandersnatch Key ($k_b$)**: First 32 bytes.
- **Ed25519 Key ($k_e$)**: Next 32 bytes.
- **BLS Key ($k_{\text{BLS}}$)**: Following 144 bytes.
- **Metadata ($k_m$)**: Last 128 bytes (e.g., hardware address).

### **Epoch Transition**

- **Key Rotation**: At each epoch's start, the pending set $\gamma_{k}$ is updated from the staging set $\iota$, excluding any keys identified as offenders (misbehaving validators).

- **Bandersnatch Ring Root ($z$)**: Updated based on the new set of Bandersnatch keys.

- **Offenders Handling**: Validator keys flagged as offenders are replaced with null keys (all zeros) to prevent them from participating in block production.

---

## 6.4. **Sealing and Entropy Accumulation**

### **Seal Requirements**

- **Seal Signature ($\mathbf{H}_s$)**: Must be a valid Bandersnatch signature corresponding to the current slot's sealing key.

- **Entropy Source**: The VRF output from the seal signature provides unbiased randomness used as a **ticket**.

### **Entropy Accumulator ($\eta$)**

- **Composition**: Maintains the current state and historical states of entropy:
  - **$\eta_0$**: Current randomness accumulator.
  - **$\eta_1$, $\eta_2$, $\eta_3$**: Historical accumulators from the last three epochs.

- **Usage**:
  - **$\eta_2$**: Ensures future entropy remains unbiased and seeds fallback mechanisms.
  - **$\eta_3$**: Used for verifying entropy during seal validation.

### **Block Header Conditions**

Depending on whether the sealing is done via a regular ticket or a fallback mechanism, different conditions must be met:

1. **Regular Seal**:
   - **Seal Signature Validity**: Must correspond to the current sealing key.
   - **Ticket Indicator ($\mathbf{T}$)**: Set to 1, marking the seal as regular.

2. **Fallback Seal**:
   - **Fallback Seal Signature Validity**: Uses a fallback key sequence.
   - **Ticket Indicator ($\mathbf{T}$)**: Set to 0, indicating fallback mode.

---

## 6.5. **The Slot Key Sequence**

### **Determining $\gamma'_\mathbf{s}$**

The next slot's sealing key sequence ($\gamma'_\mathbf{s}$) is determined based on the current block's context:

1. **New Epoch & Closing Period**:
   - If the block marks the transition to a new epoch and is within the closing period ($m \geq \mathsf{Y}$), and the ticket accumulator is full ($|\gamma_\mathbf{a}| = \mathsf{E}$):
     - **Action**: Use the ticket accumulator to set the new sealing key sequence via the sequencer function $Z$.

2. **Same Epoch**:
   - If still within the current epoch:
     - **Action**: Retain the current sealing key sequence ($\gamma_\mathbf{s}$).

3. **Fallback Scenario**:
   - **Condition**: If the above conditions aren't met (e.g., insufficient tickets).
   - **Action**: Generate a fallback sealing key sequence using the entropy accumulator and active validator keys via function $F$.

### **Functions Explained**

- **Sequencer Function $Z$**:
  - **Purpose**: Reorders the ticket sequence to ensure unpredictability.
  - **Operation**: Alternates selecting from the start and end of the input sequence.

- **Fallback Function $F$**:
  - **Purpose**: Generates a sealing key sequence when ticket accumulation fails.
  - **Operation**: Selects validator keys based on the current entropy, ensuring randomness in key selection.

---

## 6.6. **The Markers**

### **Epoch Marker ($\mathbf{H}_e$)**

- **Purpose**: Indicates the start of a new epoch and provides necessary information to update validator sets.

- **Content**:
  - **If New Epoch**: Contains the new epoch's randomness ($\eta_0$, $\eta_1$) and the list of new Bandersnatch keys.
  - **Otherwise**: Empty.

### **Winning-Tickets Marker ($\mathbf{H}_w$)**

- **Purpose**: Captures the final sequence of winning tickets at the end of the submission period.

- **Condition**:
  - **If**: The block is the first after the ticket submission period ends, and the ticket accumulator is full.
  - **Action**: Records the final sorted ticket sequence via $Z(\gamma_\mathbf{a})$.

- **Otherwise**: Empty.

### **Usage**

These markers minimize the data needed to track validator set changes and winning tickets, enabling efficient synchronization for nodes.

---

## 6.7. **The Extrinsic and Tickets**

### **Tickets Extrinsic ($\xttickets$)**

- **Definition**: A sequence of proofs submitted by validators, representing their participation in the next epoch's sealing key selection.

- **Structure**:
  - **Each Ticket**: A tuple containing an entry index ($r$) and a proof ($p$) of ticket validity via the Bandersnatch VRF.

- **Constraints**:
  - **During Submission Period ($m' < \mathsf{Y}$)**: Can include up to $\mathsf{K}$ tickets.
  - **After Submission Period ($m' \geq \mathsf{Y}$)**: Must be empty, signaling the end of ticket submissions for the epoch.

### **Ticket Identifier ($\mathbf{n}$)**

- **Extraction**: Derives the ticket identifiers from the submitted proofs in $\xttickets$.

- **Uniqueness**:
  - **Order and Uniqueness**: Tickets must be submitted in order and without duplicates.
  - **Disjointness**: New tickets cannot overlap with existing ones in the accumulator.

### **Ticket Accumulator ($\gamma'_\mathbf{a}$)**

- **Purpose**: Maintains a sorted list of the highest-scoring tickets, capped at $\mathsf{E}$ tickets per epoch.

- **Update Mechanism**:
  - **Merging**: Combines new tickets with existing ones and sorts them.
  - **Capping**: Keeps only the top $\mathsf{E}$ tickets based on their scores.

- **Validity**:
  - **Inclusion**: All submitted tickets must be part of the updated accumulator.

### **Special Case Handling**

- **Empty Extrinsic**: If no tickets are submitted ($\xttickets = []$), and it's within the same epoch, the accumulator remains unchanged.
