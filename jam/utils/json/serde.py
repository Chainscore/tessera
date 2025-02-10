from typing import Any, TypeVar, Type, Dict, Optional
from dataclasses import dataclass

T = TypeVar('T')

class JsonSerializationError(Exception):
    """Base exception for JSON serialization errors"""
    pass

class JsonDeserializationError(Exception):
    """Base exception for JSON deserialization errors"""
    pass

class JsonFieldError(JsonSerializationError):
    """Exception for field-related errors during JSON conversion"""
    def __init__(self, field_name: str, field_type: Type, message: str):
        self.field_name = field_name
        self.field_type = field_type
        super().__init__(f"Field '{field_name}' ({field_type.__name__}): {message}")

@dataclass
class JsonFieldMetadata:
    """Metadata for JSON field customization"""
    name: Optional[str] = None  # Custom JSON field name
    skip_if_none: bool = False  # Skip field if value is None
    format: Optional[str] = None  # Custom format string

class JsonSerde:
    """
    Mixin for JSON serialization/deserialization.
    This is designed to work alongside Codable without inheritance conflicts.
    """
    
    def to_json(self) -> Any:
        """Convert instance to JSON-compatible value"""
        from .codec import JsonCodec
        return JsonCodec.to_json(self)
    
    @classmethod
    def from_json(cls: Type[T], data: Any) -> T:
        """Create instance from JSON-compatible value"""
        from .codec import JsonCodec
        return JsonCodec.from_json(data, cls)
    
    @classmethod
    def __json_metadata__(cls) -> Dict[str, JsonFieldMetadata]:
        """Get JSON metadata for fields. Override to customize field handling."""
        return getattr(cls, '__json_fields__', {}) 