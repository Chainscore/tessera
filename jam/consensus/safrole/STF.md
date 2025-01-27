## Safrole Transitions:

#### 1. **Timekeeping**
⭐️ The timeslot index `tau` updates based on the block header:

$$
\tau' \equiv H_t
$$

#### 2. **Accumulate Entropy**
⭐️ The entropy $\eta_0$ is updated by incorporating the VRF output:

$$
\eta'_0 \equiv \mathcal{H}(\eta_0 \| \text{VRF}_{\text{output}})
$$


#### 3. **Ticket Accumulation**
⭐️ Tickets are validated and accumulated to determine block authorship:

$$
\gamma'_a \equiv \gamma_a \cup \{\text{new valid tickets}\} \text{ (sorted)}
$$

#### 4. **Epoch Transition**
On epoch transitions ($e' > e$), validator key rotation occurs:

$$
(\gamma'_k, \kappa', \lambda', \gamma'_z) \equiv
\begin{cases}
(\Phi(\iota), \gamma_k, \kappa, \gamma_z) & \text{if } e' > e \\
(\gamma_k, \kappa, \lambda, \gamma_z) & \text{otherwise}
\end{cases}
$$

where $\Phi(\iota)$ filters out offenders from the new validator set.

Also at epoch boundaries, the entropy values rotate:

$$
(\eta'_1, \eta'_2, \eta'_3) \equiv
\begin{cases}
(\eta_0, \eta_1, \eta_2) & \text{if } e' > e \\
(\eta_1, \eta_2, \eta_3) & \text{otherwise}
\end{cases}
$$

The slot sealing key series $\gamma_s$ is updated based on epoch changes:

$$
\gamma'_s \equiv
\begin{cases}
Z(\gamma_a) & \text{if } e' = e + 1 \text{ and } m \geq Y \\
\gamma_s & \text{if } e' = e \\
F(\eta'_2, \kappa') & \text{otherwise}
\end{cases}
$$

- ⭐️ Key rotation
- ⭐️ Remove offenders 
- ⭐️ Update ring root- $\gamma_z$
- ⭐️ Entropy updated
- ⭐️ Update slot sealing key series - $\gamma_s$