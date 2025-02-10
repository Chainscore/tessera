"""
JSON serialization/deserialization module for JAM types.

This module provides a unified way to convert JAM types to and from JSON.
It supports both base types and complex dataclasses, with customizable
field handling and metadata.

Basic usage:
    from jam.utils.codec.json import json_serializable, json_field

    @json_serializable
    @dataclass
    class MyClass:
        field1: str = json_field(name="jsonField1")
        field2: int = json_field(skip_if_none=True)

Advanced usage:
    @json_serializable
    @with_json_metadata(
        field1={'name': 'jsonField1', 'skip_if_none': True},
        field2={'format': '%Y-%m-%d'}
    )
    class MyClass:
        field1: str
        field2: datetime
"""

from .serde import (
    JsonSerde,
    JsonSerializationError,
    JsonDeserializationError,
    JsonFieldError,
    JsonFieldMetadata
)
from .codec import JsonCodec
from .decorators import (
    json_serializable,
    json_field,
    json_field_metadata,
    with_json_metadata
)

__all__ = [
    # Core interfaces
    'JsonSerde',
    'JsonCodec',
    
    # Decorators
    'json_serializable',
    'json_field',
    'json_field_metadata',
    'with_json_metadata',
    
    # Exceptions
    'JsonSerializationError',
    'JsonDeserializationError',
    'JsonFieldError',
    
    # Types
    'JsonFieldMetadata',
] 