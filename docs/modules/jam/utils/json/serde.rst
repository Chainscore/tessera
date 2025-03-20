jam.utils.jstruct.serde
==================

Base interface for JSON serialization, providing a mixin class and metadata types.

Core Components
-------------

JsonSerde
^^^^^^^^
Base mixin class that adds JSON capabilities to any class:

* to_json(): Convert instance to JSON-compatible value
* from_json(): Create instance from JSON-compatible value
* __json_metadata__(): Get field metadata

JsonFieldMetadata
^^^^^^^^^^^^^^^
Configuration class for field serialization:

* name: Custom JSON field name
* skip_if_none: Skip field if value is None
* format: Value formatting (e.g., date format)

Implementation Details
-------------------

Mixin Usage
^^^^^^^^^
Two ways to use the JsonSerde mixin:

1. Direct inheritance:

.. code-block:: python

    @dataclass
    class Point(JsonSerde):
        x: int
        y: int

2. With json_serializable decorator:

.. code-block:: python

    @json_serializable
    @dataclass
    class Point:
        x: int
        y: int

Field Metadata
^^^^^^^^^^^
Field metadata controls serialization:

.. code-block:: python

    @dataclass
    class Document(JsonSerde):
        # Custom field name
        created: datetime = json_field(
            name="createdAt"
        )
        
        # Skip None values
        tags: Optional[list[str]] = json_field(
            skip_if_none=True
        )
        
        # Both options
        metadata: dict = json_field(
            name="meta",
            skip_if_none=True
        )

Error Handling
------------

Exception Types
^^^^^^^^^^^^^
* JsonSerializationError: Base serialization error
* JsonDeserializationError: Base deserialization error
* JsonFieldError: Field-specific errors

Common Errors
^^^^^^^^^^^
1. Type mismatch during conversion
2. Missing required fields
3. Invalid field values
4. Format errors (e.g., date parsing)

API Reference
-----------

Classes
^^^^^^^
.. autoclass:: jam.utils.jstruct.serde.JsonSerde
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.utils.jstruct.serde.JsonFieldMetadata
   :members:
   :undoc-members:
   :show-inheritance:

Exceptions
^^^^^^^^^
.. autoclass:: jam.utils.jstruct.serde.JsonSerializationError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.utils.jstruct.serde.JsonDeserializationError
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: jam.utils.jstruct.serde.JsonFieldError
   :members:
   :undoc-members:
   :show-inheritance:

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    from dataclasses import dataclass
    from jam.utils.jstruct import JsonSerde

    @dataclass
    class Point(JsonSerde):
        x: int
        y: int

    point = Point(1, 2)
    data = point.to_json()  # -> {"x": 1, "y": 2}
    decoded = Point.from_json(data)  # -> Point(x=1, y=2)

Field Customization
^^^^^^^^^^^^^^^^
.. code-block:: python

    from datetime import datetime
    from typing import Optional, List

    @dataclass
    class Document(JsonSerde):
        id: str
        created: datetime = json_field(
            name="createdAt",
            format="%Y-%m-%d"
        )
        tags: Optional[List[str]] = json_field(
            skip_if_none=True
        )

    doc = Document(
        id="123",
        created=datetime.now(),
        tags=["a", "b"]
    )
    data = doc.to_json()
    # -> {
    #     "id": "123",
    #     "createdAt": "2024-02-11",
    #     "tags": ["a", "b"]
    # }

Error Handling
^^^^^^^^^^^
.. code-block:: python

    try:
        Document.from_json({
            "id": 123,  # Wrong type
            "createdAt": "invalid-date"
        })
    except JsonFieldError as e:
        print(e)  # Field 'id' (str): Expected str, got int
