jam.types.base.bit module
=========================

.. automodule:: jam.types.base.bit
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

jam.types.base.bit
===============

Bit type implementation for the JAM protocol.

Type Definition
-------------

Bit
^^^
* Single bit value (0/1)
* Used in bit sequences
* Packed bit storage
* No alignment requirements

Encoding Format
-------------

Single Bit::

    0 -> [0]  # LSB of byte
    1 -> [1]  # LSB of byte

Bit Sequences::

    [b0 b1 b2 b3 b4 b5 b6 b7]  # Packed into bytes
    LSB first within each byte

Implementation Details
-------------------

Memory Layout
^^^^^^^^^^
* Single bit storage
* Packed into bytes
* LSB first ordering
* No padding bits

Bit Operations
^^^^^^^^^^^
* Bit masking
* Bit shifting
* Bit counting
* Bit packing/unpacking

Error Handling
^^^^^^^^^^^
Common error cases:

1. Invalid value::

    if value not in (0, 1):
        raise ValueError(f"Invalid bit value: {value}")

2. Buffer underflow::

    if len(buffer) - offset < 1:
        raise BufferError("Need 1 byte for bit")

3. Position overflow::

    if bit_position >= 8:
        raise ValueError(f"Invalid bit position: {bit_position}")

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    from jam.types.base.bit import Bit

    # Create and encode
    value = Bit(1)
    encoded = value.encode()  # -> [01]

    value = Bit(0)
    encoded = value.encode()  # -> [00]

    # Decode
    decoded = Bit.decode(encoded)
    assert decoded == 0

Bit Sequences
^^^^^^^^^^
.. code-block:: python

    from jam.types.base.sequences import BitArray
    from jam.types.base.bit import Bit

    # Create 8-bit sequence
    bits = BitArray[8]([
        Bit(1), Bit(0), Bit(1), Bit(0),
        Bit(1), Bit(0), Bit(1), Bit(0)
    ])

    # Encode: packed bits
    encoded = bits.encode()  # -> [AA]  # 10101010

    # Decode
    decoded = BitArray[8].decode(encoded)
    assert [bit.value for bit in decoded] == [1,0,1,0,1,0,1,0]

Custom Types
^^^^^^^^^^
.. code-block:: python

    from dataclasses import dataclass
    from jam.types.base.bit import Bit, decodable_bit

    @decodable_bit
    @dataclass
    class Flag:
        value: int  # 0 or 1

    # Create and encode
    flag = Flag(1)
    encoded = flag.encode()  # -> [01]

    # Decode
    decoded = Flag.decode(encoded)
    assert decoded.value == 1

API Reference
-----------

Classes
^^^^^^
.. autoclass:: jam.types.base.bit.Bit
   :members:
   :undoc-members:
   :show-inheritance:

Decorators
^^^^^^^^
.. autofunction:: jam.types.base.bit.decodable_bit
