String type
==================

Type Definition
-------------

String
^^^^^
* UTF-8 encoded text
* Length-prefixed format
* Variable size encoding
* Zero-copy decoding

Encoding Format
-------------

Structure::

   [Length_Data: Int][UTF-8 bytes]

Implementation Details
-------------------

Memory Layout
^^^^^^^^^^
* Length prefix: Variable size (GEneral Int encoding)
* UTF-8 bytes: Contiguous
* No padding or alignment
* Direct buffer access

UTF-8 Handling
^^^^^^^^^^^
* Strict UTF-8 validation
* Proper code point handling
* Surrogate pair support
* Invalid sequence detection

Error Handling
^^^^^^^^^^^
Common error cases:

1. Invalid UTF-8::

    try:
        return bytes.decode('utf-8')
    except UnicodeError as e:
        raise DecodeError(f"Invalid UTF-8: {e}")

2. Buffer overflow::

    if len(buffer) - offset < needed_size:
        raise BufferError(f"Buffer too small: need {needed_size} bytes")

3. Length mismatch::

    if len(utf8_bytes) != length:
        raise ValueError(f"Length mismatch: expected {length}, got {len(utf8_bytes)}")

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    from jam.types.base.string import String

    # Create and encode
    text = String("hello")
    encoded = text.encode()
    # -> [05 68 65 6C 6C 6F]
    #    len=5, "hello"

    # Decode
    decoded = String.decode(encoded)
    assert decoded == "hello"

API Reference
-----------

Classes
^^^^^^
.. autoclass:: jam.types.base.string.String
   :members:
   :undoc-members:
   :show-inheritance:

Decorators
^^^^^^^^
.. autofunction:: jam.types.base.string.decodable_string
