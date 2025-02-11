jam.utils.codec
=============

Type-safe serialization framework implementing the JAM protocol specification.

Core Components
-------------

Codec[T]
^^^^^^^
Generic codec interface for type-safe encoding/decoding:

* encode(value: T) -> bytes
* decode(buffer: bytes) -> T
* encode_into(value: T, buffer: bytearray, offset: int) -> int
* decode_from(buffer: bytes, offset: int) -> Tuple[T, int]

Codable
^^^^^^
Base class for encodable types:

* Direct codec usage
* Sequence-based encoding
* Custom encoding logic
* JSON serialization support

Encoding Format
-------------

Length Prefixes
^^^^^^^^^^^^
* 0x00-0xFC: Direct value (1 byte)
* 0xFF: u16 value (3 bytes)
* 0xFE: u24 value (4 bytes) 
* 0xFD: u32 value (5 bytes)

Type Encoding
^^^^^^^^^^
Primitive Types:

* bool: Single byte (0=false, 1=true)
* trivial int: Fixed width unsigned integers
* general int: Variable length unsigned integers
* str: Length-prefixed UTF-8
* bytes: Length-prefixed raw bytes
* null: Zero bytes

Container Types:

* Array[T,N]: Fixed-length [T; N]
* Vector[T]: Length-prefixed [len][T...]
* Dict[K,V]: Length-prefixed sorted pairs
* Option[T]: Tagged union (0=None, 1=Some(T))
* BitSequence: Packed bits

Error Handling
------------

Exception Types
^^^^^^^^^^^^
* CodecError: Base exception class
* BufferError: Buffer operation errors
* EncodeError: Encoding failures
* DecodeError: Decoding failures

Common Error Cases
^^^^^^^^^^^^^^^
1. Buffer underflow/overflow
2. Invalid length prefixes
3. Type conversion errors
4. Sequence validation errors

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    from jam.utils.codec.primitives import IntegerCodec, StringCodec
    from jam.utils.codec.composite import VectorCodec

    # Primitive types
    u32_codec = IntegerCodec(4)
    encoded_int = u32_codec.encode(42)  # -> [2A 00 00 00]
    decoded_int = u32_codec.decode(encoded_int)  # -> 42

    string_codec = StringCodec()
    encoded_str = string_codec.encode("hello")  # -> [05 68 65 6C 6C 6F]
    decoded_str = string_codec.decode(encoded_str)  # -> "hello"

    # Container types
    vec_codec = VectorCodec(int, u32_codec)
    encoded_vec = vec_codec.encode([1, 2])  # -> [02 01 00 00 00 02 00 00 00]
    decoded_vec = vec_codec.decode(encoded_vec)  # -> [1, 2]

Custom Types
^^^^^^^^^^
.. code-block:: python

    from dataclasses import dataclass
    from jam.utils.codec.decorators import decodable_dataclass

    @decodable_dataclass
    @dataclass
    class Point:
        x: int
        y: int

    point = Point(1, 2)
    encoded = point.encode()  # -> [01 00 00 00 02 00 00 00]
    decoded = Point.decode(encoded)  # -> Point(x=1, y=2)

Error Handling
^^^^^^^^^^^
.. code-block:: python

    try:
        u32_codec.decode(bytes([0x01]))  # Too short
    except BufferError as e:
        print(f"Expected {e.expected} bytes, got {e.actual}")

    try:
        string_codec.decode(bytes([0xFF, 0x01]))  # Invalid UTF-8
    except DecodeError as e:
        print(f"Failed to decode string: {e}")

Submodules
---------

.. toctree::
   :maxdepth: 2

   codec
   codable
   errors
   primitives/index
   composite/index
   decorators/index

Module Contents
-------------

.. automodule:: jam.utils.codec
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
