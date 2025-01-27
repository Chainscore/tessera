# Safrole Notes - Block Production and Chain Growth

### **Overview**

- **Hybrid Consensus Mechanism**: Safrole is built upon a hybrid consensus system akin to Polkadot's BABE/GRANDPA. This combines two consensus algorithms to leverage their strengths.

- **Purpose of Safrole**:
  - **Rate Limiting**: Controls how quickly new blocks are produced.
  - **Fork Prevention**: Aims to avoid the creation of multiple competing blocks (forks) that have the same number of ancestor blocks.

### **Key Features**

- **Six-Second Timeslots**: Time is divided into six-second intervals called timeslots. Each timeslot allows only one validator (from a predefined set) to author a block.

- **Validator Anonymity**: The specific validator assigned to a future timeslot remains anonymous, enhancing security and reducing predictability.

- **Entropy Pool Generation**: Safrole generates a high-quality pool of randomness (entropy) that other protocol components can utilize, ensuring unpredictability and fairness.

### **State Management**

- **Core State ($\gamma$)**: Safrole maintains its own state, which is separate from the rest of the protocol but interacts through specific variables:
  - **$\iota$**: Prospective set of validator keys.
  - **$\kappa$**: Active set of validator keys.
  - **$\tau$**: Most recent block's timeslot index.
  - **$\eta$**: Entropy accumulator.

### **Sealing Keys and Ring VRF**

- **Sealing Keys ($\mathsf{E}$)**: For each epoch, Safrole generates a sequence of sealing keys—one for each potential block in that epoch.

- **Block Headers**: Each block header includes:
  - **Timeslot Index ($\mathbf{H}_t$)**: Indicates the specific timeslot.
  - **Seal Signature ($\mathbf{H}_s$)**: Signed by the sealing key for that timeslot.

- **Ring VRF with Bandersnatch Curve**:
  - **Functionality**: Ensures that a sealing key is selected from the validator set without revealing which validator it corresponds to.
  - **Outcome**: Produces a **ticket**, an unbiased deterministic hash used to select the sealing key.

---

## 6.1. **Timekeeping**

### **Timeslot Index ($\tau$)**

- **Definition**: $\tau$ represents the most recent block's timeslot index, indicating the number of six-second intervals since the $\text{Jam}$ Common Era began.

- **Epoch and Slot Phase**:
  - **Epoch Index ($e$)**: Derived from dividing $\tau$ by the epoch length ($\mathsf{E}$).
  - **Slot Phase Index ($m$)**: The remainder of $\tau$ divided by $\mathsf{E}$, indicating the slot's position within the current epoch.

### **Purpose**

- **Epoch Transition Detection**: By tracking $\tau$, the protocol can easily identify when a new epoch starts and manage validator rotations accordingly.

---

## 6.2. **Safrole Basic State ($\gamma$)**

### **State Components**

$\gamma$ is divided into four parts:

1. **$\gamma_\mathbf{k}$**: Pending set of validator keys for the next epoch.
2. **$\gamma_z$**: Root composed of Bandersnatch keys for the upcoming epoch's validators.
3. **$\gamma_\mathbf{s}$**: Current epoch's sealing key sequence.
4. **$\gamma_\mathbf{a}$**: Ticket accumulator holding the highest-scoring tickets for the next epoch.

### **Tickets ($\mathbb{C}$)**

- **Structure**: Each ticket consists of:
  - **Ticket Identifier ($\mathbf{y}$)**: A high-entropy, unbiasable 32-byte sequence.
  - **Entry-Index ($r$)**: An integer representing the ticket's position.

- **Purpose**: Tickets are used to select validators for block production slots in the upcoming epoch.

### **Seal Signatures**

- **Requirement**: Every block header must include a valid seal signature ($\mathbf{H}_s$), proving that the block was authored by an authorized validator.

---

## 6.3. **Key Rotation**

### **Validator Key Sets**

- **Active Set ($\kappa$)**: Validators currently authorized to produce blocks and perform validation.
- **Staging Set ($\iota$)**: Validators slated to become active in the next epoch.
- **Pending Set ($\gamma_k$)**: Temporarily holds the next epoch's validator keys, reset at each epoch's start.

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
