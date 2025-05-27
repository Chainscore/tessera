jam.utils.codec.codable
===================

Base class for types that can encode and decode themselves.

Interface
--------

Codable[T]
^^^^^^^^
.. code-block:: python

    class Codable(Generic[T]):
        def __init__(self, 
                    codec: Optional[Codec[T]] = None,
                    enc_sequence: Optional[Callable[[], list[Any]]] = None):
            self.codec = codec
            self.enc_sequence = enc_sequence

Usage Patterns
------------

Direct Codec
^^^^^^^^^^
Use a specific codec for encoding/decoding:

.. code-block:: python

    class Point(Codable[tuple[int, int]]):
        def __init__(self, x: int, y: int):
            super().__init__(codec=TupleCodec(IntCodec(), IntCodec()))
            self.x = x
            self.y = y
            
        def value(self) -> tuple[int, int]:
            return (self.x, self.y)

Sequence Encoding
^^^^^^^^^^^^^^
Encode as a sequence of values:

.. code-block:: python

    class Point(Codable[tuple[int, int]]):
        def __init__(self, x: int, y: int):
            super().__init__(enc_sequence=lambda: [self.x, self.y])
            self.x = x
            self.y = y

Custom Encoding
^^^^^^^^^^^^
Implement custom encode/decode logic:

.. code-block:: python

    class Point(Codable[tuple[int, int]]):
        def encode(self) -> bytes:
            return bytes([self.x, self.y])
            
        @classmethod
        def decode(cls, buffer: bytes) -> 'Point':
            return cls(buffer[0], buffer[1])

Implementation Details
-------------------

Value Property
^^^^^^^^^^^
The value property provides the raw value for encoding:

.. code-block:: python

    @property
    def value(self) -> T:
        """Get the value to encode."""
        if hasattr(self, 'get_value'):
            return self.get_value()
        return self._value

Encoding Process
^^^^^^^^^^^^^
1. Get value via property
2. Use codec if provided
3. Use sequence if provided
4. Call custom encode()

Decoding Process
^^^^^^^^^^^^^
1. Use codec if provided
2. Use sequence if provided
3. Call custom decode()
4. Set value property

Error Handling
^^^^^^^^^^^
Common error cases:

1. Missing codec/sequence:
   
   .. code-block:: python
   
       if not self.codec and not self.enc_sequence:
           raise CodecError("No codec or sequence provided")

2. Invalid sequence:
   
   .. code-block:: python
   
       if not all(isinstance(x, Codable) for x in sequence):
           raise CodecError("Sequence contains non-Codable values")

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    class Point(Codable[tuple[int, int]]):
        def __init__(self, x: int, y: int):
            super().__init__(codec=TupleCodec(IntCodec(), IntCodec()))
            self.x = x
            self.y = y
            
        def value(self) -> tuple[int, int]:
            return (self.x, self.y)

    point = Point(1, 2)
    encoded = point.encode()  # -> [01 00 00 00 02 00 00 00]
    decoded = Point.decode(encoded)  # -> Point(1, 2)

Sequence Example
^^^^^^^^^^^^^
.. code-block:: python

    class Vector(Codable[list[int]]):
        def __init__(self, *components: int):
            super().__init__(enc_sequence=lambda: list(components))
            self.components = components

    vec = Vector(1, 2, 3)
    encoded = vec.encode()  # -> [03 01 02 03]
    decoded = Vector.decode(encoded)  # -> Vector(1, 2, 3)

API Reference
-----------

.. automodule:: jam.utils.codec.codable
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
