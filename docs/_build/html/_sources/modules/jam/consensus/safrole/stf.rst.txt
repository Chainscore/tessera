Safrole STF
============================

Overview
--------

The Safrole State Transition Function (STF) defines how the protocol state evolves with each block. It handles four main types of transitions:

1. Timekeeping
-------------
Updates the timeslot index (τ) based on the block header timestamp.

2. Entropy Accumulation
--------------------
Updates the entropy (η₀) by incorporating VRF outputs from block headers:

.. math::

   η'₀ ≡ H(η₀ ‖ VRF_{output}(H_v))

3. Ticket Processing
-----------------
Handles ticket extrinsics in each block:

* Validates ticket entries (entry index, VRF signature)
* Verifies tickets are not duplicated
* Ensures proper ordering by VRF output
* Accumulates valid tickets into state

4. Epoch Transitions
-----------------
Manages state updates at epoch boundaries:

* Rotates validator keys: (γ'ₖ, κ', λ') ≡ (Φ(ι), γₖ, κ)
* Updates entropy values: (η'₁, η'₂, η'₃) ≡ (η₀, η₁, η₂)
* Updates slot sealing keys based on conditions
* Computes new ring root from validator set

API Reference
-----------

.. automodule:: jam.consensus.safrole.stf
   :members:
   :undoc-members:
   :show-inheritance: 