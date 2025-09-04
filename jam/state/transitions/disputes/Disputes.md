# Disputes State Transitions

## 1. Disputes Transition

The disputes transition updates the state based on the disputes extrinsic from a block. It processes verdicts, culprits, and faults, updates the state's ψ component, and removes wrong targets from the core (ρ) array. If any error is encountered during the process, a `DisputesError` is raised with the appropriate error code.

Formally, the transition is defined as:

$$
\text{new\_state} \equiv \text{Disputes.transition(pre\_state, block)}
$$

### Constraints

- **Valid Verdicts Constraint**: A verdict that is solely valid (i.e., all votes are positive) must have at least one fault and two culprits..
- **Sorting Requirements**:
  - Verdicts must be sorted by target in ascending order.
  - Votes within verdicts must be sorted by validator index in ascending order.
  - Culprits and faults must be sorted by key in ascending order.
- **Signature Verification**: All signatures (for verdicts, faults, and culprits) must be valid according to the defined ed25519 verification logic.

### Function Signature

- **Arguments**:
  - `pre_state`: The state before the transition.
  - `block`: The block containing the disputes extrinsic.
- **Returns**:
  - The updated state after processing disputes. The ρ array is updated with the correct targets, and the disputes state (ψ) is updated.
  - In case of an error, a `DisputesError` is raised with an appropriate error code.

## 2. Valid Age

The valid age of a dispute is determined by the current epoch (from `kappa`) and the previous epoch (from `lambda`). Its acceptable range is defined as follows:

- Calculate the current epoch as:
  $$
  \text{current\_epoch} = \frac{\text{new\_state.tau}}{\text{EPOCH\_LENGTH}}
  $$
- The valid age must satisfy:
  $$
  \text{current\_epoch} - 1 \leq \text{valid\_age} \leq \text{current\_epoch}
  $$

For further details, see the [Graypaper documentation](https://graypaper.fluffylabs.dev/#/5b732de/12dc0012f900).

## 3. ψ (Psi) Sets

The disputes state component ψ consists of four sets:

$$
\psi = (\psi_g, \psi_b, \psi_w, \psi_o)
$$

- **good_set (ψ_g)**: Stores keys of validators with good verdicts.(positive votes=2/3V +1)
- **bad_set (ψ_b)**: Stores keys of validators with bad verdicts.(positive votes=0)
- **wonky_set (ψ_w)**: Stores keys of validators whose verdicts are uncertain (wonky).(positive votes=1/3V)
- **offenders_set (ψ_o)**: Stores keys of validators who have been determined to be offenders (e.g., based on faults or culprits).

## 4. Verify Signature

Fault, culprit, and vote signatures (using ed25519) must be verified with the following function:

$$
\text{Disputes.verify\_signature(key, message, target, signature)}
$$

This function is used to ensure that all signatures in verdicts, faults, and culprits are valid.

## 5. Validate Verdicts

- **Sorting**: Verify that verdicts are sorted by target in ascending order.
- **Judgement and Age**: Check if verdicts are already judged and if their age is within the valid range.

## 6. Validate Faults and Culprits

- **Sorting**:
  - Faults must be sorted by key (ascending order).
  - Culprits must be sorted by key (ascending order).
- **Duplication**: Ensure that culprits are not already reported.
  
## 7. Process Verdicts with Constraints

- **Vote Sorting**: Verify that votes within each verdict are sorted by validator index in ascending order.
- **Contradictory Faults**: Ensure that fault verdicts are not contradictory.
- **Vote Count Classification**: Count the positive votes to classify a verdict as good, bad, or wonky.  
  - If the vote split is unexpected, throw a `bad_vote_split` error.
- **Minimum Count Checks**: Verify that the number of faults and culprits meets the required counts:
  - Solely valid verdicts must have at least one fault and two culprits.

## 8. Remove Wrong Targets from the ρ Array

- After processing the disputes, remove any work reports from the ρ array that have been judged as wrong (i.e., targets that appear in the bad or wonky sets).
$$
\forall c \in \mathbb{N}_C : \rho^\dagger[c] = 
\begin{cases}
\emptyset & \text{if } \{(\mathcal{H}(\rho[c]_w), t) \in V, t < \lfloor\frac{2}{3}V\rfloor\} \\
\rho[c] & \text{otherwise}
\end{cases}
$$


## 9. Update Disputes State and Return New State

- Update the ψ sets and the ρ array in the state according to the processed disputes.
- **Note**: There is a TODO to change the ρ array when new types are implemented.
- Finally, return the updated state.

---

This documentation provides a high-level overview of the disputes state transition logic, its formal constraints, and the steps involved in processing disputes. Each step ensures that the disputes data (verdicts, faults, and culprits) is validated, signatures are checked, and the state is updated accordingly.

