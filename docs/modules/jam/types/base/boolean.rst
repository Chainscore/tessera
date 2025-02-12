jam.types.base.boolean
===================

Boolean type implementation for the JAM protocol.

Type Definition
-------------

Boolean
^^^^^^
* Single byte representation
* Zero/one encoding
* No padding or alignment
* Direct buffer access

Encoding Format
-------------

Values::

    false -> [00]
    true  -> [01]

Any non-zero value is considered true when decoding.

Implementation Details
-------------------

Memory Layout
^^^^^^^^^^
* Single byte storage
* No alignment requirements
* Direct buffer manipulation
* Zero-copy decoding

Value Handling
^^^^^^^^^^^
* Strict encoding (0/1 only)
* Lenient decoding (any non-zero = true)
* No implicit conversions
* Type safety checks

Error Handling
^^^^^^^^^^^
Common error cases:

1. Type mismatch::

    if not isinstance(value, bool):
        raise TypeError(f"Expected bool, got {type(value)}")

2. Buffer underflow::

    if len(buffer) - offset < 1:
        raise BufferError("Need 1 byte for boolean")

3. Invalid value::

    if value not in (0, 1):
        raise ValueError(f"Invalid boolean value: {value}")

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    from jam.types.base.boolean import Boolean

    # Create and encode
    value = Boolean(True)
    encoded = value.encode()  # -> [01]

    value = Boolean(False)
    encoded = value.encode()  # -> [00]

    # Decode
    decoded = Boolean.decode(encoded)
    assert decoded is False

Buffer Operations
^^^^^^^^^^^^^
.. code-block:: python

    # Direct buffer manipulation
    buffer = bytearray(1)
    written = Boolean(True).encode_into(buffer, 0)  # -> 1
    value, read = Boolean.decode_from(buffer, 0)  # -> (True, 1)


API Reference
-----------

Classes
^^^^^^
.. autoclass:: jam.types.base.boolean.Boolean
   :members:
   :undoc-members:
   :show-inheritance:

Decorators
^^^^^^^^
.. autofunction:: jam.types.base.boolean.decodable_boolean
