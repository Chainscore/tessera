Gamma State Component
==================

The Gamma (γ) state component is a critical part of the Safrole consensus protocol that manages validator-related state. It consists of four main subcomponents:

GammaK (γₖ)
----------
Tracks the current validator set, storing validator public keys, VRF keys, and weights.

GammaA (γₐ)
----------
Accumulates tickets during an epoch, maintaining an ordered list of valid ticket submissions.

GammaZ (γᵧ)
----------
Stores the ring root for the current epoch, used for signature verification.

GammaS (γₛ)
----------
Manages slot sealers, either using the highest scoring tickets or fallback validator keys.

API Reference
-----------

.. automodule:: jam.consensus.safrole.gamma
   :members:
   :undoc-members:
   :show-inheritance:
