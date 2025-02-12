Safrole State Transition Function
============================

Overview
--------

The Safrole State Transition Function (STF) defines how the protocol state evolves with each block. It handles four main types of transitions:
|

1. Timekeeping
-------------
Updates the timeslot index (τ) based on the block header timestamp:

.. math::

   \tau' \equiv H_t

|

2. Entropy Accumulation  
--------------------
Updates the entropy (η₀) by incorporating VRF outputs from block headers:

.. math::

   \eta'_0 \equiv \mathcal{H}(\eta_0 \| \text{VRF}_{\text{output}}(H_v))

|

3. Ticket Processing
-----------------
Handles ticket extrinsics in each block:

* Validates ticket entries (entry index, VRF signature)
* Verifies tickets are not duplicated 
* Ensures proper ordering by VRF output
* Accumulates valid tickets into state:

.. math::

   \gamma'_a \equiv sorted(\gamma_a \cup \{\text{new valid tickets}\})

|

4. Epoch Transitions
-----------------
Manages state updates at epoch boundaries:

* Rotates validator keys:

.. math::

   (\gamma'_k, \kappa', \lambda') \equiv (\Phi(\iota), \gamma_k, \kappa)

where :math:`\Phi(\iota)` filters out offenders from the new validator set.

* Updates entropy values:

.. math:: 

   (\eta'_1, \eta'_2, \eta'_3) \equiv (\eta_0, \eta_1, \eta_2)

* Updates slot sealing keys based on conditions:

.. math::

   \gamma'_s \equiv
   \begin{cases}
   Z(\gamma_a) & \text{if } e' = e + 1 \text{ and } m \geq Y \\\\
   \gamma_s & \text{if } e' = e \\\\  
   F(\eta'_2, \kappa') & \text{otherwise}
   \end{cases}

* Computes new ring root from validator set:

.. math::

   \gamma_z \equiv O(k_b \text{ for } k \in \gamma'_k) \text{ (sorted by } k_b)

|

API Reference
-----------

.. automodule:: jam.consensus.safrole.safrole
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
