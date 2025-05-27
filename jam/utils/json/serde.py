"""JSON serialization interface."""

from typing import Any, TypeVar, Type, Dict, Optional
from dataclasses import dataclass

T = TypeVar("T")


class JsonSerializationError(Exception):
    """Base exception for JSON serialization errors."""

    pass


class JsonDeserializationError(Exception):
    """Base exception for JSON deserialization errors."""

    pass


class JsonFieldError(JsonSerializationError):
    """Field-specific JSON conversion error."""

    def __init__(self, field_name: str, field_type: Type, message: str):
        self.field_name = field_name
        self.field_type = field_type
        super().__init__(f"Field '{field_name}' ({field_type.__name__}): {message}")


@dataclass
class JsonFieldMetadata:
    """Field customization metadata."""

    name: Optional[str] = None
    skip_if_none: bool = False
    format: Optional[str] = None


class JsonSerde:
    """Base mixin for JSON serialization."""

    def to_json(self) -> Any:
        """Convert to JSON-compatible value."""
        from .codec import JsonCodec

        return JsonCodec.to_json(self)

    @classmethod
    def from_json(cls: Type[T], data: Any) -> T:
        """Create from JSON-compatible value."""
        from .codec import JsonCodec
        # print("data->", data)

        return JsonCodec.from_json(data, cls)

    @classmethod
    def __json_metadata__(cls) -> Dict[str, JsonFieldMetadata]:
        """Get JSON metadata for fields."""
        return getattr(cls, "__json_fields__", {})
