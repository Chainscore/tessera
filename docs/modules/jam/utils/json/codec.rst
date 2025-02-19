jam.utils.json.codec
==================

Core JSON serialization engine that handles type-safe conversion between JAM types and JSON.

Type Resolution
-------------

Type Resolution Order
^^^^^^^^^^^^^^^^^
1. None type checking
2. Primitive type validation
3. Optional type unwrapping
4. Container type handling
5. Dataclass field processing
6. Custom type conversion

Type Mapping
^^^^^^^^^^
Primitive Types:

* bool -> true/false
* int -> number
* str -> string
* bytes -> hex string
* Null -> null

Container Types:

* Array[T] -> [T, ...]
* Vector[T] -> [T, ...]
* Dict[K,V] -> {K: V, ...}
* Option[T] -> T | null
* Enum -> value | name

Custom Types:

* @json_serializable -> object
* JsonSerde -> custom conversion

Implementation Details
-------------------

Type Conversion
^^^^^^^^^^^^^
The codec processes types in this order:

1. None values -> null
2. Primitive types -> direct conversion
3. Sequences -> JSON arrays
4. Mappings -> JSON objects
5. Dataclasses -> JSON objects with field processing
6. Objects with value property -> convert value
7. Objects with to_json() -> custom conversion

Field Processing
^^^^^^^^^^^^^
For dataclasses, fields are processed with:

1. Type validation
2. Custom field names
3. Null value handling
4. Value formatting
5. Default value handling

Error Handling
------------

Exception Types
^^^^^^^^^^^^^
* JsonSerializationError: Base serialization error
* JsonDeserializationError: Base deserialization error
* JsonFieldError: Field-specific errors

Common Error Cases
^^^^^^^^^^^^^^^
1. Type mismatch during deserialization
2. Missing required fields
3. Invalid field values
4. Unsupported types

API Reference
-----------

JsonCodec
^^^^^^^^
.. autoclass:: jam.utils.json.codec.JsonCodec
   :members:
   :undoc-members:
   :show-inheritance:

Functions
^^^^^^^^
.. autofunction:: jam.utils.json.codec.is_optional_type

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    from jam.utils.json import JsonCodec
    
    # Primitive types
    JsonCodec.to_json(42)  # -> 42
    JsonCodec.to_json("hello")  # -> "hello"
    JsonCodec.to_json(True)  # -> true
    
    # Container types
    JsonCodec.to_json([1, 2, 3])  # -> [1, 2, 3]
    JsonCodec.to_json({"a": 1})  # -> {"a": 1}

Dataclass Handling
^^^^^^^^^^^^^^^
.. code-block:: python

    @dataclass
    class Point:
        x: int
        y: int
        
    point = Point(1, 2)
    data = JsonCodec.to_json(point)  # -> {"x": 1, "y": 2}
    decoded = JsonCodec.from_json(data, Point)  # -> Point(x=1, y=2)

Custom Types
^^^^^^^^^^
.. code-block:: python

    class Vector:
        def __init__(self, x, y):
            self.value = {"x": x, "y": y}
            
    vec = Vector(1, 2)
    data = JsonCodec.to_json(vec)  # -> {"x": 1, "y": 2}

Error Handling
^^^^^^^^^^^
.. code-block:: python

    try:
        JsonCodec.from_json("not a dict", Point)
    except JsonDeserializationError as e:
        print(e)  # Expected dict for Point, got str
