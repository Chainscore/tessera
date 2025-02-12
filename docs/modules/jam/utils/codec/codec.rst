jam.utils.codec.codec
=================

Core codec interface for type-safe encoding and decoding.

Interface
--------

Codec[T]
^^^^^^^
.. code-block:: python

    class Codec(Generic[T], ABC):
        @abstractmethod
        def encode(self, value: T) -> bytes: ...
        
        @abstractmethod
        def decode(self, buffer: bytes) -> T: ...
        
        @abstractmethod
        def encode_into(self, value: T, buffer: bytearray, offset: int) -> int: ...
        
        @abstractmethod
        def decode_from(self, buffer: Union[bytes, bytearray], offset: int) -> Tuple[T, int]: ...

Methods
------

encode
^^^^^
Convert a value to bytes:

* value: The value to encode
* returns: Encoded bytes

decode
^^^^^
Convert bytes back to a value:

* buffer: The bytes to decode
* returns: Decoded value

encode_into
^^^^^^^^^
Write encoded bytes into a buffer:

* value: The value to encode
* buffer: Target buffer to write into
* offset: Starting position in buffer
* returns: Number of bytes written

decode_from
^^^^^^^^^
Read and decode bytes from a buffer:

* buffer: Source buffer to read from
* offset: Starting position in buffer
* returns: (decoded_value, bytes_read)

Implementation
------------

Buffer Operations
^^^^^^^^^^^^^
Direct buffer manipulation for efficient I/O:

.. code-block:: python

    def encode_into(self, value: T, buffer: bytearray, offset: int) -> int:
        encoded = self.encode(value)
        buffer[offset:offset + len(encoded)] = encoded
        return len(encoded)

    def decode_from(self, buffer: bytes, offset: int) -> Tuple[T, int]:
        # Read length prefix
        length = self._read_length(buffer, offset)
        # Extract value bytes
        value_bytes = buffer[offset:offset + length]
        # Decode value
        value = self.decode(value_bytes)
        return value, length

Error Handling
^^^^^^^^^^^
Common error cases:

1. Buffer underflow:
   
   .. code-block:: python
   
       if len(buffer) - offset < needed:
           raise BufferError(needed, len(buffer) - offset)

2. Invalid data:
   
   .. code-block:: python
   
       try:
           return self._decode_value(buffer)
       except ValueError as e:
           raise DecodeError(str(e))

3. Type mismatch:
   
   .. code-block:: python
   
       if not isinstance(value, self._value_type):
           raise EncodeError(f"Expected {self._value_type}, got {type(value)}")

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    class IntegerCodec(Codec[int]):
        """Codec for encoding and decoding 4-byte integers."""
        def encode(self, value: int) -> bytes:
            return value.to_bytes(4, 'little')
            
        def decode(self, buffer: bytes) -> int:
            return int.from_bytes(buffer, 'little')

    codec = IntegerCodec()
    encoded = codec.encode(42)  # -> [2A 00 00 00]
    decoded = codec.decode(encoded)  # -> 42

Buffer Operations
^^^^^^^^^^^^^
.. code-block:: python

    buffer = bytearray(8)
    codec.encode_into(42, buffer, 0)  # -> 4 bytes written
    value, bytes_read = codec.decode_from(buffer, 0)  # -> (42, 4)

API Reference
-----------

.. automodule:: jam.utils.codec.codec
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
