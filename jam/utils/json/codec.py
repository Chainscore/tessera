"""Core JSON codec implementation."""

from collections.abc import Sequence, Mapping
from dataclasses import is_dataclass, fields
from functools import lru_cache
import sys
from types import UnionType
from typing import Any, Dict, Type, TypeVar, Union, get_args, get_origin
from .serde import JsonSerializationError, JsonDeserializationError, JsonFieldError

T = TypeVar("T")


class JsonCodec:
    """Core JSON serialization engine."""

    @staticmethod
    def to_json(obj: Any) -> Any:
        """Convert object to JSON-compatible value."""
        if obj is None:
            return None

        # Handle primitive types
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # Handle sequences (lists, tuples)
        if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
            return [JsonCodec.to_json(item) for item in obj]

        # Handle mappings (dicts)
        if isinstance(obj, Mapping):
            return {str(k): JsonCodec.to_json(v) for k, v in obj.items()}

        # Handle dataclasses
        if is_dataclass(obj):
            return JsonCodec._dataclass_to_json(obj)

        # Handle objects with a value property
        if hasattr(obj, "value"):
            return JsonCodec.to_json(obj.value)

        raise JsonSerializationError(f"Cannot serialize object of type {type(obj)}")

    @staticmethod
    def from_json(data: Any, target_type: Type[T]) -> T:
        """Convert JSON-compatible value to target type."""
        try:
            # Handle None
            if data is None:
                if target_type is type(None):
                    return None
                raise JsonDeserializationError(f"Cannot convert None to {target_type}")

            # Handle primitive types
            if target_type in (str, int, float, bool):
                if not isinstance(data, target_type):
                    raise JsonDeserializationError(
                        f"Expected {target_type}, got {type(data)}"
                    )
                return data

            # Handle optional types
            if is_optional_type(target_type):
                if data is None:
                    return None
                return JsonCodec.from_json(data, get_args(target_type)[0])

            # Handle sequences
            if isinstance(target_type, (list, tuple, Sequence)):
                if len(get_args(target_type)) == 0:
                    return target_type(data)
                else:
                    return target_type([JsonCodec.from_json(item, get_args(target_type)[0]) for item in data])

            # Handle mappings
            if target_type is Sequence:
                key_type, value_type = get_args(target_type)
                return target_type(
                    {
                        JsonCodec.from_json(k, key_type): JsonCodec.from_json(
                            v, value_type
                        )
                        for k, v in data.items()
                    }
                )

            # Handle dataclasses
            if is_dataclass(target_type):
                return JsonCodec._dataclass_from_json(data, target_type)

            try:
                if target_type is Dict:
                    return dict(data)
                return target_type(data)
            except Exception as e:
                raise JsonDeserializationError(
                    f"Cannot deserialize to type {target_type}. Full error: {e}"
                )

        except (TypeError, ValueError) as e:
            raise JsonDeserializationError(
                f"Error deserializing to {target_type}: {str(e)}"
            )

    @staticmethod
    @lru_cache(maxsize=128)
    def _get_dataclass_fields(cls: Type) -> Dict[str, Any]:
        """Get and cache dataclass field information."""
        return {
            field.name: {
                "type": field.type,
                "metadata": getattr(field, "metadata", {}),
                "default": field.default or None,
                "default_factory": field.default_factory,
            }
            for field in fields(cls)
        }

    @staticmethod
    def _dataclass_to_json(obj: Any) -> Dict[str, Any]:
        """Convert dataclass instance to JSON dict"""
        result = {}
        field_info = getattr(obj, "metadata", {})

        for field in fields(obj):
            field_name = field.name
            field_type = field.type
            
            meta_json_name = field_info.get(field_name, {}).get("json_name", field_name)
            meta_skip_if_none = field_info.get(field_name, {}).get("skip_if_none", False)
            meta_default = field_info.get(field_name, {}).get("default", None)

            value = getattr(obj, field_name)
            # Skip None values if specified in metadata
            if value is None and meta_skip_if_none:
                continue
            
            # Use custom field name if specified
            json_name = meta_json_name
            try:
                result[json_name] = to_json(value)
            except Exception as e:
                raise JsonFieldError(field_name, field_type, str(e))
            
        return result

    @staticmethod
    def _dataclass_from_json(data: Dict[str, Any], cls: Type[T]) -> T:
        """Convert JSON dict to dataclass instance."""
        if not isinstance(data, dict):
            raise JsonDeserializationError(
                f"Expected dict for {cls.__name__}, got {type(data)}"
            )

        field_info = getattr(cls, "metadata", {})
        field_values = {}

        # Loop through all fields in the dataclass to fill data for each field
        for field in fields(cls):
            field_name = field.name
            field_type = field.type
            meta_json_name = field_info.get(field_name, {}).get("json_name", field_name)
            meta_skip_if_none = field_info.get(field_name, {}).get("skip_if_none", False)
            meta_default = field_info.get(field_name, {}).get("default", None)
            # Field processing

            # If the field is not present in the JSON data, check if it has an alternative name in the metadata
            # Or if it has a default value, or if it is optional
            if field_name not in data:
                # Check if it has an alternative name in the metadata. if the alt value exists
                if meta_json_name in data:
                    if data[meta_json_name] is None and meta_default is not None:
                        field_values[field_name] = meta_default
                    else:
                        field_values[field_name] = from_json(data[meta_json_name], field_type)
                    # field_values[field_name] = from_json(data[meta_json_name], field_type)
                # Check if the field has a default value
                elif meta_default is not None:
                    field_values[field_name] = meta_default
                # Check if the field is optional
                elif meta_skip_if_none or is_optional_type(field_type):
                    field_values[field_name] = None
                # Raise an error if the field is not optional and has no default value
                else:
                    raise JsonFieldError(
                        field_name, field_type, "Missing required field"
                    )
            # If the field is present in the JSON data
            # Wrap and assign the value to the field
            else:
                try:
                    if data[meta_json_name] is None and meta_default is not None:
                        field_values[field_name] = meta_default
                    else:
                        field_values[field_name] = from_json(data[meta_json_name], field_type)

                    # field_values[field_name] = from_json(data[meta_json_name], field_type)

                    # Not check the type of the field
                    if not isinstance(field_values[field_name], field_type):
                        raise JsonFieldError(
                            field_name,
                            field_type,
                            f"Expected {field_type}, got {type(field_values[field_name])}",
                        )
                except Exception as e:
                    raise JsonFieldError(field_name, field_type, str(e))
        return cls(**field_values)

def from_json(data: Any, target_type: Type[T]) -> T:
    """Convert JSON-compatible value to target type."""
    if hasattr(target_type, "from_json"):
        return target_type.from_json(data)
    else:
        return JsonCodec.from_json(data, target_type)
    
def to_json(obj: Any) -> Any:
    """Convert object to JSON-compatible value."""
    if hasattr(obj, "to_json"):
        return obj.to_json()
    else:
        return JsonCodec.to_json(obj)

def is_optional_type(tp) -> bool:
    """Check if type hint is Optional[T]."""
    origin = get_origin(tp)
    args = get_args(tp)

    if origin is Union or (sys.version_info >= (3, 10) and origin is UnionType):
        return type(None) in args
    return False
