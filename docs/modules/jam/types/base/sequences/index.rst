jam.types.base.sequences
=====================

Sequence type implementations for the JAM protocol.

Type Definitions
--------------

Array Types
^^^^^^^^^
* Array[T, N]: Fixed-length array of any custom type T with size N
* BitArray[N]: Fixed-length array of bits
* ByteArray[N]: Fixed-length array of bytes

Vector Types
^^^^^^^^^^
* Vector[T]: Dynamic-length array of any custom type T
* Bytes: Dynamic-length byte array

Encoding Format
-------------

Fixed-length Arrays
^^^^^^^^^^^^^^^^
No length prefix, just elements::

    Array[u8, 3]([1,2,3]) -> [01 02 03]
    BitArray[8]([1,0,1,0,1,0,1,0]) -> [AA]  # 10101010
    ByteArray[2]([1,2]) -> [01 02]

Dynamic Vectors
^^^^^^^^^^^^
Length prefix followed by elements::

    Vector[u8]([1,2]) -> [02 01 02]  # len=2, elements=[1,2]
    Bytes([1,2,3]) -> [03 01 02 03]  # len=3, bytes=[1,2,3]

Implementation Details
-------------------

Memory Layout
^^^^^^^^^^
* Arrays: Contiguous memory, no gaps
* Vectors: Length prefix + contiguous elements
* Bit arrays: Packed bits, no padding
* Byte arrays: Raw bytes, no encoding

Size Validation
^^^^^^^^^^^^
* Fixed arrays: Exact size required
* Bit arrays: Bit count must match
* Vectors: Dynamic size with max limit
* Byte arrays: Size validation on fixed variants

Error Handling
^^^^^^^^^^^
Common error cases:

1. Size mismatch::

    if len(value) != self.size:
        raise ValueError(f"Expected {self.size} elements, got {len(value)}")

2. Invalid element type::

    if not isinstance(element, element_type):
        raise TypeError(f"Invalid element type: {type(element)}")

3. Buffer overflow::

    if len(buffer) - offset < needed_size:
        raise BufferError(f"Buffer too small: need {needed_size} bytes")

Examples
-------

Fixed Arrays
^^^^^^^^^^
.. code-block:: python

    from jam.types.base.sequences import Array
    from jam.types.base.integers import U8

    # Create fixed array of 3 U8 values
    @decodable_array(U8, 3)
    class U8_3_Array(Array[U8, 3]): ...

    arr = U8_3_Array([1, 2, 3])

    # Encode: [elements...]
    encoded = arr.encode()  # -> [01 02 03]
    
    # Decode
    decoded = U8_3_Array.decode(encoded)  # -> [1, 2, 3]

Bit Arrays
^^^^^^^^
.. code-block:: python

    from jam.types.base.sequences import BitArray
    
    # Create 8-bit array
    @decodable_bit_array(8)
    class Bit8Array(BitArray[8]): ...

    bits = Bit8Array([1,0,1,0,1,0,1,0])
    
    # Encode: packed bits
    encoded = bits.encode()  # -> [AA]  # 10101010
    
    # Decode
    decoded = Bit8Array.decode(encoded)  # -> [1,0,1,0,1,0,1,0]

Dynamic Vectors
^^^^^^^^^^^^
.. code-block:: python

    from jam.types.base.sequences import Vector
    from jam.types.base.integers import U32
    
    # Create vector of u32
    @decodable_vector(U32)
    class U32Vector(Vector[U32]): ...

    vec = U32Vector([1, 2, 3])
    
    # Encode: [len][elements...]
    encoded = vec.encode()
    # -> [03 01 00 00 00 02 00 00 00 03 00 00 00]
    
    # Decode
    decoded = U32Vector.decode(encoded)  # -> [1, 2, 3]

Byte Arrays
^^^^^^^^^
.. code-block:: python

    from jam.types.base.sequences import ByteArray32, Bytes
    
    # Fixed size
    fixed = ByteArray32(bytes([1] * 32))
    encoded = fixed.encode()  # -> [01 01 ... 01] (32 bytes)
    
    # Dynamic size
    dynamic = Bytes(bytes([1, 2, 3]))
    encoded = dynamic.encode()  # -> [03 01 02 03]

API Reference
-----------

Classes
^^^^^^
.. autoclass:: jam.types.base.sequences.array.Array
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.sequences.vector.Vector
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.sequences.bytes.bit_array.BitArray
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.sequences.bytes.byte_array.ByteArray
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.sequences.bytes.bytes.Bytes
   :members:
   :undoc-members:
   :show-inheritance:

Decorators
^^^^^^^^
.. autofunction:: jam.types.base.sequences.array.decodable_array

.. autofunction:: jam.types.base.sequences.vector.decodable_vector

.. autofunction:: jam.types.base.sequences.bytes.bit_array.decodable_bit_array

Submodules
---------

.. toctree::
   :maxdepth: 2

   array
   vector
   bytes/index
