jam.types.base.choices
===================

Choice type implementations for the JAM protocol.

Type Definitions
--------------

Choice[T]
^^^^^^^
* Tagged union type
* Discriminant + value encoding
* Type-safe variant selection
* Compile-time variant checking

Option[T]
^^^^^^^
* Nullable type wrapper
* Special case of Choice
* None or Some(T)
* Zero overhead for None

Encoding Format
-------------

Choice[T]
^^^^^^^
Tagged union format::

    [Tag: varint][Value: varies]

* Tag: Index of the variant (0-based)
* Value: Encoded variant value

Option[T]
^^^^^^^
Special encoding::

    None -> [00]  # Single byte
    Some(value) -> [01][Encoded value]

Implementation Details
-------------------

Memory Layout
^^^^^^^^^^
* Tag: Variable size integer
* Value: Variable size
* No padding between tag and value
* Alignment preserved for value

Type Safety
^^^^^^^^^
* Variant types checked at compile time
* Runtime type validation
* Tag range validation
* Value type checking

Error Handling
^^^^^^^^^^^
Common error cases:

1. Invalid variant::

    if tag >= len(variants):
        raise ValueError(f"Invalid variant tag: {tag}")

2. Type mismatch::

    if not isinstance(value, variant_type):
        raise TypeError(f"Expected {variant_type}, got {type(value)}")

3. Buffer overflow::

    if len(buffer) - offset < tag_size:
        raise BufferError(f"Buffer too small for tag")

Examples
-------

Choice Type
^^^^^^^^^
.. code-block:: python

    from dataclasses import dataclass
    from jam.types.base.choices import Choice, decodable_choice
    from jam.types.base.integers import U32
    from jam.types.base.string import String

    # Define variants
    @dataclass
    class Number:
        value: U32

    @dataclass
    class Text:
        value: String

    # Create choice type
    @decodable_choice(Number, Text)
    class Value:
        variant: Choice[Number, Text]

    # Create and encode number variant
    num = Value(Number(U32(42)))
    encoded = num.encode()  # -> [00 2A 00 00 00]

    # Create and encode text variant
    text = Value(Text(String("hello")))
    encoded = text.encode()  # -> [01 05 68 65 6C 6C 6F]

Option Type
^^^^^^^^^
.. code-block:: python

    from jam.types.base.choices import Option, decodable_option
    from jam.types.base.integers import U32

    # Define optional type
    @decodable_option(U32)
    class OptionalNumber:
        value: Option[U32]

    # None case
    none = OptionalNumber(None)
    encoded = none.encode()  # -> [00]

    # Some case
    some = OptionalNumber(U32(42))
    encoded = some.encode()  # -> [01 2A 00 00 00]

    # Decode
    decoded = OptionalNumber.decode(encoded)
    assert decoded.value == U32(42)

API Reference
-----------

Classes
^^^^^^
.. autoclass:: jam.types.base.choices.Choice
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.types.base.choices.Option
   :members:
   :undoc-members:
   :show-inheritance:

Decorators
^^^^^^^^
.. autofunction:: jam.types.base.choices.decodable_choice

.. autofunction:: jam.types.base.choices.decodable_option 