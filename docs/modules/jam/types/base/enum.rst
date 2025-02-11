jam.types.base.enum
=================

Enum type implementation for the JAM protocol.

Type Definition
-------------

Enum
^^^^
* Extends Python's built-in Enum type
* Adds encoding/decoding capabilities
* JSON serialization support
* Type-safe variant selection

Encoding Format
-------------

Structure::

    [Index: u8]  # Single byte index into enum variants

* Index: Zero-based index of the enum variant in declaration order
* Maximum 256 variants supported (u8 limit)
* Deterministic encoding based on declaration order

Implementation Details
-------------------

Memory Layout
^^^^^^^^^^
* Single byte storage
* No padding or alignment
* Direct buffer access
* Zero-copy decoding

Variant Handling
^^^^^^^^^^^^
* Variants ordered by declaration
* Index-based encoding
* Name and value preservation
* Type safety checks

JSON Support
^^^^^^^^^^
* Bidirectional conversion
* Value-based serialization
* Name-based deserialization
* Error handling

Error Handling
^^^^^^^^^^^
Common error cases:

1. Too many variants::

    if index > 255:
        raise ValueError("Enum index is too large to encode into a single byte")

2. Invalid variant::

    if variant_name not in cls._member_names_:
        raise ValueError(f"Invalid variant: {variant_name}")

3. JSON conversion error::

    if value not in cls.__members__.values():
        raise JsonDeserializationError(f"Invalid value: {value}")

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    from jam.types.base.enum import Enum, decodable_enum

    @decodable_enum
    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    # Create and encode
    color = Color.RED
    encoded = color.encode()  # -> [00]  # First variant

    # Decode
    decoded = Color.decode(encoded)
    assert decoded == Color.RED

JSON Handling
^^^^^^^^^^
.. code-block:: python

    # Value-based JSON
    json_data = Color.RED.to_json()  # -> 1
    color = Color.from_json(1)  # -> Color.RED

    # Name-based JSON
    color = Color.from_json("RED")  # -> Color.RED


API Reference
-----------

Classes
^^^^^^
.. autoclass:: jam.types.base.enum.Enum
   :members:
   :undoc-members:
   :show-inheritance:

Decorators
^^^^^^^^
.. autofunction:: jam.types.base.enum.decodable_enum
