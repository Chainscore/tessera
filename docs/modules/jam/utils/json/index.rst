JsonSerde
============

Type-safe JSON serialization framework integrated with the JAM codec system.

Core Components
-------------

JsonCodec
^^^^^^^^
Core serialization engine that handles type-safe conversion between JAM types and JSON:

* Type inference and validation
* Primitive type conversion
* Container type handling
* Dataclass support
* Custom type conversion

JsonSerde
^^^^^^^^
Base mixin for adding JSON capabilities to classes:

* to_json() for serialization
* from_json() for deserialization
* Field metadata support
* Inheritance-based usage

Decorators
^^^^^^^^^
* @json_serializable: Add JSON capabilities to classes
* @json_field: Configure field serialization
* @with_json_metadata: Bulk field configuration

Type Resolution
-------------

Primitive Types
^^^^^^^^^^^^^
* bool -> true/false
* int -> number
* str -> string
* bytes -> hex string
* Null -> null

Container Types
^^^^^^^^^^^^^
* Array[T] -> [T, ...]
* Vector[T] -> [T, ...]
* Dict[K,V] -> {K: V, ...}
* Option[T] -> T | null
* Enum -> value | name

Custom Types
^^^^^^^^^^
* @json_serializable -> object
* JsonSerde -> custom conversion

Error Handling
------------
* JsonSerializationError: Base serialization error
* JsonDeserializationError: Base deserialization error
* JsonFieldError: Field-specific errors

Usage Examples
------------

Basic Usage
^^^^^^^^^
.. code-block:: python

    from dataclasses import dataclass
    from jam.utils.jstruct import json_serializable, json_field

    @json_serializable
    @dataclass
    class Point:
        x: int
        y: int = json_field(name="yCoord")

    point = Point(1, 2)
    data = point.to_json()  # -> {"x": 1, "yCoord": 2}
    decoded = Point.from_json(data)  # -> Point(x=1, y=2)

Field Customization
^^^^^^^^^^^^^^^^
.. code-block:: python

    @json_serializable
    @dataclass
    class Document:
        id: str
        tags: list[str] = json_field(skip_if_none=True)
        metadata: dict = json_field(name="meta")

    doc = Document("123", ["a", "b"], {"key": "value"})
    # -> {
    #     "id": "123",
    #     "tags": ["a", "b"],
    #     "meta": {"key": "value"}
    # }

Error Handling
^^^^^^^^^^^
.. code-block:: python

    try:
        Point.from_json({"x": "not_a_number", "y": 2})
    except JsonFieldError as e:
        print(e)  # Field 'x' (int): Expected int, got str

Submodules
---------

.. toctree::
   :maxdepth: 2

   codec
   serde
   decorators

Module Contents
--------------

.. automodule:: jam.utils.jstruct
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__
