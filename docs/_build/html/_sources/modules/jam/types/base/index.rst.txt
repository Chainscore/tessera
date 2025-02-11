Base Types
=============

Core data type implementations with binary encoding capabilities.

Type Implementations
-----------------

1. Integers (:mod:`.integers`):
   * Fixed-width unsigned integers: U8, U16, U32, U64 (little-endian)
   * Signed integers: I8, I16, I32, I64 (little-endian)
   * Variable-width unsigned integers: Int (compact encoding for values < 2⁶⁴)

2. Sequences (:mod:`.sequences`):
   * Fixed-length arrays: Array[T, N]
      * BitArray[Bit, N]: Fixed size packed bits
         * Byte[Bit,8]: 8-bit array
      * ByteArray[Bytes, N]: Fixed-length byte array
   * Dynamic vectors: Vector[T]
      * Bytes: Variable length byte array

3. Containers:
   * Dictionary[K, V]: ordered key-value pairs
   * Choice[T]: discriminated union
   * Option[T]: nullable values

4. Basic Types:
   * Bit: single bit
   * String: UTF-8 with length prefix
   * Boolean: single byte (0/1)
   * Null: zero-sized type

Encoding Formats
--------------

Fixed-width Integer::

    I32(42) -> [2A 00 00 00]  # Little-endian

Variable-width Integer::

    Int(42) -> [2A]          # Single byte for small values
    Int(1000) -> [E8 07]     # Two bytes for larger values

String::

    String("abc") -> [03 61 62 63]  # Length prefix + UTF-8 bytes

Vector::

    Vector[u8]([1,2]) -> [02 01 02]  # Length prefix + elements

Dictionary::

    Dict{"a": 1} -> [01 01 61 01]  # Size + (key_len + key + value)...

Technical Details
--------------

Memory Layout:
    * All types are packed (no padding)
    * Explicit alignment when needed
    * Direct buffer manipulation
    * Zero-copy where possible

Type Parameters:
    * Generic over element types
    * Proper variance annotations
    * Compile-time size checks
    * Runtime validation

Error Handling:
    * Range validation for integers
    * UTF-8 validation for strings
    * Buffer overflow checks
    * Type mismatch detection

Examples
-------

Integer types::

    from jam.types.base.integers import Int32, VarInt
    
    # Fixed-width
    value = I32(42)
    assert value.encode() == bytes([42, 0, 0, 0])
    
    # Variable-width
    value = Int(1000)
    assert value.encode() == bytes([232, 7])  # 0xE8 0x07

Sequence types::

    from jam.types.base.sequences import Vector
    from jam.types.base.integers import Int8
    
    # Create I32 vector
    @decodable_vector(I32)
    class I32Vector(Vector[I32]): ...
    
    vec = I32Vector([1, 2, 3])
    # Encode: [len: varint][items: [u8; len]]
    encoded = vec.encode()
    assert encoded == bytes([3, 1, 2, 3])
    
    # Decode
    decoded, size = I32Vector.decode_from(encoded)
    assert decoded == [1, 2, 3]
    assert size == 4  # Total bytes read

Container types::

    from jam.types.base.dictionary import Dict
    from jam.types.base.string import String
    from jam.types.base.integers import Int8
    
    # Create dictionary of String keys and Int8 values
    @decodable_dictionary(String, Int8)
    class StringInt8Dict(Dict[String, Int8]): ...

    d = StringInt8Dict({
        "a": 1,
        "b": 2
    })
    
    # Encode: [size][key_len key value]...
    encoded = d.encode()
    
    # Decode
    decoded, _ = StringInt8Dict.decode_from(encoded)
    assert decoded == {"a": 1, "b": 2}

API Reference
-----------

Integer Types:
    * U8, U16, ... U256: Fixed-width unsigned integers
    * I8, I16, ... I256: Fixed-width signed integers
    * Int: Variable-width unsigned integer

Sequence Types:
    * Array[T, N]: Fixed-length array
        * BitField[Bit, N]: Fixed size packed bits
            * Byte[Bit,8]: 8-bit array
        * ByteArray[Bytes, N]: Fixed-length byte array
    * Vector[T]: Dynamic array
        * Bytes: Variable length byte array

Choice Types:
    * Choice[T]: Tagged union
    * Option[T]: Optional value

Container Types:
    * Dict[K, V]: Key-value mapping

Basic Types:
    * String: UTF-8 string
    * Boolean: True/False
    * Null: Unit type

Submodules
---------

.. toctree::
   :maxdepth: 2

   integers
   sequences/index
   dictionary
   choices
   string
   boolean
   bit
   null

Module Contents
-------------

.. automodule:: jam.types.base
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
