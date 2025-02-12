Introduction
============

Welcome to Tessera, a Python implementation of JAM (Join Accumulate Machine). Tessera is designed to provide a performant, type-safe, and scalable blockchain infrastructure with a focus on user-friendly interfaces and developer experience.

Key Features
-----------

* **Type-safe Serialization**: Custom codec system for handling protocol types
* **Consensus Mechanisms**: Implementation of Safrole and GRANDPA protocols
* **State Transition Functions**: Efficient state transitions
* **Network Layer**: P2P communication with async I/O
* **Execution Environment**: Polkadot Virtual Machine (PVM) for generic smart contracts

Architecture Overview
------------------

Tessera is built with a modular architecture:

* **Core Protocol**: Implements the JAM protocol specification
* **State Layer**: Manages blockchain state and transitions
* **Consensus Layer**: Handles block production and finality
* **Network Layer**: Manages peer connections and data sync
* **Execution Layer**: Runs the Polkadot Virtual Machine (PVM)

Development Status
---------------

Tessera is currently under active development. While core components are functional, some features are still being implemented and the API may change.

Getting Started
-------------

To get started with Tessera:

1. Follow the :doc:`installation` guide to set up your development environment
2. Read through the :doc:`quickstart` guide for basic usage
3. Explore the testing guide for development practices
4. Check out the Core Concepts section for detailed documentation

Contributing
----------

We welcome contributions! Please see our :doc:`CONTRIBUTING` guide for:

* Code style guidelines
* Development workflow
* Testing requirements
* Documentation standards 