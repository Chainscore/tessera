Authorization
============

Overview
--------
The authorization module handles the state transition logic for the authorization component of the JAM protocol. It defines how the authorization state evolves with each block.

Key Components
-------------

Authorization
^^^^^^^^^^^^
The main class that implements the authorization state transition function.

* transition(pre_state, block) -> State
   - Updates the authorization state based on the block
   - Pops executed authorizers from alpha 
   - Pushes new authorizers from phi to alpha

State Components
^^^^^^^^^^^^^^
The authorization transition function operates on these state components:

* alpha: Current authorizer set
* phi: Future authorizer set

Transition Logic
--------------
For each core:

1. Pop the executed authorizer from alpha
2. If the block has a guarantee for this core, use the authorizer from the guarantee
3. Push the authorizer from phi[core][block.slot] to alpha

This ensures authorizers are updated based on the block and future authorizer schedule.

Authorization State Transition
----------------------------
The state transition for a block involves:

* Modifying alpha by placing a new authorization into the pool from the queue and removing the oldest authorization from the pool
* New items are added to the queue from the accumulation (handled by the Accumulate STF)

Note: The Authorization STF should be handled after the Accumulate STF to ensure proper sequencing.

Usage Example
------------
.. code-block:: python

    from jam.authorization import Authorization
    from jam.state import State
    from jam.types import Block

    pre_state = State(...)
    block = Block(...)

    post_state = Authorization.transition(pre_state, block)

API Reference
------------

.. automodule:: jam.authorization.authorization
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
