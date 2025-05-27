Chain Specifications
====================

The Chain Specification is a configuration that defines all core constants of the JAM Chain.
While the chain itself has fixed parameters as defined in the Graypaper, alternative configurations
can be useful for testing and local deployments.

Configuration Parameters
------------------------
Each chain specification defines the following parameters (with shorthand identifiers):

- **chain**  
  The name of the spec.

- **num_validators (V)**  
  The number of validators.

- **num_cores (C)**  
  The number of cores.

- **slot_duration (P)**  
  Slot time duration in seconds.

- **epoch_duration (E)**  
  The number of slots in an epoch.

- **contest_duration (Y)**  
  The epoch in which the ticket contest ends.  
  *Constraint*: Y > 0 and Y < E

- **tickets_per_validator (N)**  
  The maximum number of tickets each validator can submit. This must be configurable
  to ensure that a 2/3+1 majority of validators can complete the ticket contest successfully.  
  *Constraint*: ((2/3) * V + 1) * N >= E

- **rotation_period (R)**  
  The rotation period of validator-core assignments, measured in timeslots.

- **max_tickets_per_extrinsic (K)**  
  The maximum number of tickets which may be submitted in a single extrinsic.  
  *Constraint*: K > 0

Predefined Configurations
-------------------------
The `jam.chainspec` module provides several preset configurations via the `JamConfig`
class. These include:

- `JamConfig.tiny()`  
- `JamConfig.small()`  
- `JamConfig.medium()`  
- `JamConfig.large()`  
- `JamConfig.xlarge()`  
- `JamConfig.xlarge2()`  
- `JamConfig.xlarge3()`  
- `JamConfig.full()`

You can obtain a configuration by calling `JamConfig.from_chain(chain_name)`, where
`chain_name` is one of the available specification names. The configuration is typically
selected using the environment variable `JAM_CHAIN_SPEC` (defaulting to "tiny" if not specified).

.. automodule:: jam.chainspec
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
