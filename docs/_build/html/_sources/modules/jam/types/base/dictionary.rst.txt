jam.types.base.dictionary module
================================

.. automodule:: jam.types.base.dictionary
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

jam.types.base.dictionary
=====================

Dictionary type implementation for the JAM protocol.

Type Definition
-------------

Dictionary[K, V]
^^^^^^^^^^^^^
* K: Key type (must be Codable)
* V: Value type (must be Codable)
* Ordered key-value pairs
* Deterministic encoding

Encoding Format
-------------

Structure::

    [Length_Tag: varint][Length_Data: varies][Pairs...]
    where each Pair is:
        [Encoded Key][Encoded Value]

Length encoding::

    0x00-0xFC: Direct value (1 byte)
    0xFF: u16 value (3 bytes)
    0xFE: u24 value (4 bytes)
    0xFD: u32 value (5 bytes)

Pairs are sorted by encoded key bytes for deterministic encoding.

Implementation Details
-------------------

Memory Layout
^^^^^^^^^^
* Length prefix: Variable size
* Key-value pairs: Contiguous
* Keys and values: Variable size
* No padding between pairs

Sorting
^^^^^
Keys are sorted by their encoded bytes:

.. code-block:: python

    def _sort_pairs(pairs):
        return sorted(
            pairs,
            key=lambda x: x[0].encode()
        )

Size Calculation
^^^^^^^^^^^^^
Total size is sum of:

1. Length prefix size
2. Encoded key sizes
3. Encoded value sizes

Error Handling
^^^^^^^^^^^
Common error cases:

1. Invalid key type::

    if not isinstance(key, Codable):
        raise TypeError(f"Key must be Codable, got {type(key)}")

2. Invalid value type::

    if not isinstance(value, Codable):
        raise TypeError(f"Value must be Codable, got {type(value)}")

3. Buffer overflow::

    if len(buffer) - offset < needed_size:
        raise BufferError(f"Buffer too small: need {needed_size} bytes")

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    from jam.types.base.dictionary import Dict
    from jam.types.base.string import String
    from jam.types.base.integers import U32

    # Create dictionary
    @decodable_dictionary(String, U32)
    class StringU32Dict(Dict[String, U32]): ...

    d = StringU32Dict({
       String("a"): U32(1),
       String("b"): U32(2)
    })

    # Encode
    encoded = d.encode()
    # -> [02 01 61 01 00 00 00 01 62 02 00 00 00]
    #    len=2, "a"->1, "b"->2

    # Decode
    decoded = StringU32Dict.decode(encoded)
    assert decoded == {String("a"): U32(1), String("b"): U32(2)}

API Reference
-----------

Classes
^^^^^^
.. autoclass:: jam.types.base.dictionary.Dict
   :members:
   :undoc-members:
   :show-inheritance:

Decorators
^^^^^^^^
.. autofunction:: jam.types.base.dictionary.decodable_dictionary
