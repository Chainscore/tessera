jam.types.base.integers
====================

Integer type implementations for the JAM protocol.

Type Definitions
--------------

Fixed-width Types
^^^^^^^^^^^^^
* U8: 8-bit unsigned integer
* U16: 16-bit unsigned integer
* U32: 32-bit unsigned integer
* U64: 64-bit unsigned integer
* U128: 128-bit unsigned integer
* U256: 256-bit unsigned integer
* I8: 8-bit signed integer
* I16: 16-bit signed integer
* I32: 32-bit signed integer
* I64: 64-bit signed integer
* I128: 128-bit signed integer
* I256: 256-bit signed integer

Variable-width Type
^^^^^^^^^^^^^^^^
* Int: Variable-width unsigned integer that supports values < 2⁶⁴

Encoding Format
-------------

Fixed-width Integers
^^^^^^^^^^^^^^^^^
Little-endian byte order::

    U8(42)    -> [2A]
    U16(42)   -> [2A 00]
    U32(42)   -> [2A 00 00 00]
    U64(42)   -> [2A 00 00 00 00 00 00 00]
    U128(42)  -> [2A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00]
    U256(42)  -> [2A 00 ... 00] (32 bytes)

Variable-width Integer
^^^^^^^^^^^^^^^^^^
Compact encoding for values < 2⁶⁴::

    0x00-0xFC           -> [value]                      # 1 byte
    0x00-0xFFFF         -> [XX value_lo value_hi]       # 3 bytes
    0x00-0xFFFFFF       -> [XX value0 value1 value2]    # 4 bytes
    0x00-0xFFFFFFFF     -> [XX value0..value3]          # 5 bytes

Implementation Details
-------------------

Memory Layout
^^^^^^^^^^
* Fixed-width types use native integer types
* No padding bytes
* Explicit alignment for larger types
* Direct buffer access for efficiency

Range Validation
^^^^^^^^^^^^^
* Unsigned only (no negative values)
* Maximum value checks
* Overflow detection
* Size validation

Error Handling
^^^^^^^^^^^
Common error cases:

1. Value out of range::

    if value > max_value:
        raise ValueError(f"Value {value} exceeds maximum {max_value}")

2. Buffer underflow::

    if len(buffer) - offset < size:
        raise BufferError(f"Need {size} bytes, have {len(buffer) - offset}")

3. Invalid encoding::

    if prefix not in (0xFF, 0xFE, 0xFD) and value > 0xFC:
        raise DecodeError(f"Invalid prefix {prefix} for value {value}")

Examples
-------

Fixed-width Usage
^^^^^^^^^^^^^
.. code-block:: python

    from jam.types.base.integers import U32

    # Create and encode
    value = U32(42)
    encoded = value.encode()  # -> [2A 00 00 00]

    # Decode
    decoded = U32.decode(encoded)  # -> 42

    # Buffer operations
    buffer = bytearray(4)
    written = value.encode_into(buffer, 0)  # -> 4
    decoded, read = U32.decode_from(buffer, 0)  # -> (42, 4)

Variable-width Usage
^^^^^^^^^^^^^^^^
.. code-block:: python

    from jam.types.base.integers import Int

    # Small values use 1 byte
    value = Int(42)
    encoded = value.encode()  # -> [2A]

    # Larger values use more bytes
    value = Int(1000)
    encoded = value.encode()  # -> [_XX_ E8 03]

    # Decode
    decoded = Int.decode(encoded)  # -> 1000

API Reference
-----------

Classes
^^^^^^
.. autoclass:: jam.types.base.integers.U8
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.integers.U16
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.integers.U32
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.integers.U64
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.integers.U128
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.integers.U256
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.integers.Int
   :members:
   :undoc-members:
   :show-inheritance:
