# Disputes State Transitions:

## 1. **Disputes Transition**

$$
    \text{new\_state} \equiv \text{Disputes.transition(pre\_state, block)}
$$


###   Transition the state with Disputes logic, enforcing verdict/fault/culprit constraints.

        Processes verdicts, culprits, and faults from the disputes extrinsic, updates the
        state's psi component, removes the wrong targets from the core(rho) array and ensures the following constraints:

        Formal constraints:
        - Solely valid verdicts require at least one fault.
        - Solely invalid verdicts require at least two culprits.
        - Verdicts/faults must be sorted by target and votes as per the validator index and culprits must be sorted by key.
        - Verdicts/faults/culprits signatures must be valid.

        Args:
            pre_state: State before transition
            block: Block containing disputes extrinsic

        Returns:
            - Updated state after processing disputes (rho array updated with correct targets and disputes state updated)
            - If any error is encountered, raise a DisputesError with the appropriate error code

## 2. **Valid Age**

The valid age is the current epoch(kappa) and the previous epoch (lambda)
Its range should be current_epoch = new_state.tau // EPOCH_LENGTH 
    current_epoch - 1 <= valid_age <= current_epoch

https://graypaper.fluffylabs.dev/#/5b732de/12dc0012f900


## 3. **Psi sets**
### psi consits of 4 sets:
$$\psi= (\psi_g, \psi_b, \psi_w, \psi_o)$$
### update psi:
- good_set(stores keys of good validators)
- bad_set(stores keys of bad validators)
- wonky_set(stores keys of wonky validators)
- offenders_set(stores keys of offenders validators)

## 4. **Verify Signature**

Faults and Culprits and Vote signatures(ed25519) are verified as per their logic with the help of the following function:

$$
\text{Disputes.verify\_signature(key, message, target, signature)}
$$

## 5. **Validate verdicts**

- Verify verdicts are sorted by target (ascending order)
- Check if verdicts are already judged and validate age

## 6. **Validate faults and culprits**

- Verify faults are sorted by target (ascending order)
- Verify culprits are sorted by key (ascending order)
- Check if culprits are already reported

## 7. **Process verdicts with constraints**

- Verify votes are sorted by index (ascending order)
- Verify Fault verdicts are not contradictory
- Count positive votes and put it as good/bad/wonky or throw it as "bad_vote_split" error
- Check the fault/culprit> required_counts

## 8. **Remove wrong targets from the rho array**

- Removed wrong targets from the rho array

## 9. **Update of the Disputes states and return the new state**

- Update the Disputes states
- TODO: Change the rho array when the new types are implemented.
- Return the new state