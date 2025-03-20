jam.utils.jstruct.decorators module
================================

Decorators for adding JSON serialization capabilities to classes.

Core Decorators
-------------

@json_serializable
^^^^^^^^^^^^^^^
Adds JSON serialization to a class:

* Adds to_json() and from_json() methods
* Makes class inherit from JsonSerde
* Preserves existing inheritance
* Handles dataclass conversion

@json_field
^^^^^^^^^
Configures field serialization:

* name: Custom JSON field name
* skip_if_none: Skip None values
* Integrates with dataclass fields

@with_json_metadata
^^^^^^^^^^^^^^^^
Bulk configuration of field metadata:

* Configure multiple fields at once
* Supports all field options
* Must be applied before @dataclass

Implementation Details
-------------------

Class Transformation
^^^^^^^^^^^^^^^^^
The @json_serializable decorator:

1. Makes class a dataclass if not already
2. Adds JsonSerde to base classes
3. Preserves class attributes and methods
4. Caches type hints for validation

Field Configuration
^^^^^^^^^^^^^^^
Field metadata is stored in dataclass field.metadata:

.. code-block:: python

    @dataclass
    class Point:
        x: int = json_field(name="xCoord")
        # field.metadata = {"json_name": "xCoord"}

Error Cases
---------

Missing Type Annotations
^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    @json_serializable  # Error: no type annotations
    class Point:
        x = 1  # Missing annotation

Invalid Field Names
^^^^^^^^^^^^^^^
.. code-block:: python

    @with_json_metadata(
        missing="value"  # Error: field not found
    )
    class Document:
        id: str

Wrong Decorator Order
^^^^^^^^^^^^^^^^^
.. code-block:: python

    @dataclass  # Error: wrong order
    @json_serializable
    class Point:
        x: int

API Reference
-----------

Decorators
^^^^^^^^
.. autofunction:: jam.utils.jstruct.decorators.json_serializable

.. autofunction:: jam.utils.jstruct.decorators.json_field

.. autofunction:: jam.utils.jstruct.decorators.with_json_metadata

.. autofunction:: jam.utils.jstruct.decorators.json_field_metadata

Examples
-------

Basic Usage
^^^^^^^^^
.. code-block:: python

    from dataclasses import dataclass
    from jam.utils.jstruct import json_serializable, json_field

    @json_serializable
    @dataclass
    class Point:
        x: int = json_field(name="xCoord")
        y: int = json_field(name="yCoord")

    point = Point(1, 2)
    data = point.to_json()  # -> {"xCoord": 1, "yCoord": 2}

Field Configuration
^^^^^^^^^^^^^^^
.. code-block:: python

    @json_serializable
    @with_json_metadata(
        created={"name": "createdAt"},
        tags={"skip_if_none": True}
    )
    @dataclass
    class Document:
        id: str
        created: datetime
        tags: Optional[list[str]] = None

    doc = Document("123", datetime.now(), ["a", "b"])
    # -> {
    #     "id": "123",
    #     "createdAt": "2024-02-11",
    #     "tags": ["a", "b"]
    # }
