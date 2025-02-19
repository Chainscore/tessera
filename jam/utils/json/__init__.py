"""
JSON serialization framework integrated with JAM codec system.

Core:
* JsonCodec: Type-safe conversion engine
* JsonSerde: Base mixin for JSON capabilities
* JsonFieldMetadata: Field configuration

Type Resolution:
* bool -> true/false
* int -> number
* str -> string
* bytes -> hex string
* Null -> null
* Array[T] -> [T, ...]
* Vector[T] -> [T, ...]
* Dict[K,V] -> {K: V, ...}
* Option[T] -> T | null
* Enum -> value | name
* @json_serializable -> object
* JsonSerde -> custom conversion
"""

from .serde import (
    JsonSerde,
    JsonSerializationError,
    JsonDeserializationError,
    JsonFieldError,
    JsonFieldMetadata,
)
from .codec import JsonCodec
from .decorators import (
    json_serializable,
    json_field,
    json_field_metadata,
    with_json_metadata,
)

__all__ = [
    # Core interfaces
    "JsonSerde",
    "JsonCodec",
    # Decorators
    "json_serializable",
    "json_field",
    "json_field_metadata",
    "with_json_metadata",
    # Exceptions
    "JsonSerializationError",
    "JsonDeserializationError",
    "JsonFieldError",
    # Types
    "JsonFieldMetadata",
]
