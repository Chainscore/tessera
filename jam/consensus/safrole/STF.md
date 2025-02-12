## Safrole State Transitions:

#### 1. **Timekeeping**
The timeslot index `tau` updates based on the block header:

$$
\tau' \equiv H_t
$$

#### 2. **Accumulate Entropy**
The entropy $\eta_0$ is updated by incorporating the VRF output:

$$
\eta'_0 \equiv \mathcal{H}(\eta_0 \| \text{VRF}_{\text{output}}(H_v))
$$


#### 3. **Ticket Accumulation**
On every block, we get ticket extrinsics which are TicketEnvelope[], 
each TicketEnvelope consists of entry_index and a valid Ring VRF signature.

3.1. Validate ticket extrinsics

- Make sure the entry index is less than TICKET_ENTRIES_PER_VALIDATOR
- Verify the VRF signature
- Check if the ticket is not already accumulated
- Make sure the extrinsic is ordered by VRF output of the signature

3.2 Accumulate of valid tickets

- For each - convert TicketEnvelope to TicketBody (by generating a VRF output 
of the signature which gives ticketBody.id)
- Add to accumulator and sort them tickets

$$
\gamma'_a \equiv sorted(\gamma_a \cup \{\text{new valid tickets}\})
$$

#### 4. **Epoch Transition**

4.1 Key Rotation

On epoch transitions ($e' > e$), validator key rotation occurs:

$$
(\gamma'_k, \kappa', \lambda') \equiv
(\Phi(\iota), \gamma_k, \kappa)
$$

where $\Phi(\iota)$ filters out offenders from the new validator set.

4.2 Entropy updation

Also at epoch boundaries, the entropy values rotate:

$$
(\eta'_1, \eta'_2, \eta'_3) \equiv
(\eta_0, \eta_1, \eta_2)
$$

4.3 Slot sealing key series

The slot sealing key series $\gamma_s$ is updated based on epoch changes:

$$
\gamma'_s \equiv
\begin{cases}
Z(\gamma_a) & \text{if } e' = e + 1 \text{ and } m \geq Y \\
\gamma_s & \text{if } e' = e \\
F(\eta'_2, \kappa') & \text{otherwise}
\end{cases}
$$

4.4 Update Ring Root

$$
\gamma_z \equiv
O(k_b \text{ for } k \in \gamma'_k) \text{(sorted by k_b)}
$$
