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
            if target_type is list:
                return target_type([item for item in data])

            # Handle mappings
            if target_type is dict:
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
                "default": field.default,
                "default_factory": field.default_factory,
            }
            for field in fields(cls)
        }

    @staticmethod
    def _dataclass_to_json(obj: Any) -> Dict[str, Any]:
        """Convert dataclass instance to JSON dict"""
        result = {}
        field_info = JsonCodec._get_dataclass_fields(type(obj))

        for field_name, info in field_info.items():
            value = getattr(obj, field_name)
            # Skip None values if specified in metadata
            if value is None and info["metadata"].get("skip_if_none", False):
                continue

            # Use custom field name if specified
            json_name = info["metadata"].get("json_name", field_name)
            try:
                result[json_name] = JsonCodec.to_json(value)
            except Exception as e:
                raise JsonFieldError(field_name, info["type"], str(e))

        return result

    @staticmethod
    def _dataclass_from_json(data: Dict[str, Any], cls: Type[T]) -> T:
        """Convert JSON dict to dataclass instance."""
        if not isinstance(data, dict):
            raise JsonDeserializationError(
                f"Expected dict for {cls.__name__}, got {type(data)}"
            )

        field_info = JsonCodec._get_dataclass_fields(cls)
        field_values = {}

        for field_name, info in field_info.items():
            # Check both original and custom field names
            json_name = info["metadata"].get("json_name", field_name)
            skip_if_none = info["metadata"].get("skip_if_none", False)

            if json_name not in data:
                if skip_if_none or is_optional_type(info["type"]):
                    field_values[field_name] = None
                elif is_optional_type(info["type"]):
                    field_values[field_name] = None
                elif info["default"] is not None:  # Has default value
                    field_values[field_name] = info["default"]
                elif info["default_factory"] is not None:
                    field_values[field_name] = info["default_factory"]()
                else:
                    raise JsonFieldError(
                        field_name, info["type"], "Missing required field"
                    )
            else:
                try:
                    if hasattr(info["type"], "from_json"):
                        field_values[field_name] = info["type"].from_json(
                            data[json_name]
                        )
                    else:
                        field_values[field_name] = data[json_name]

                    # Not check the type of the field
                    if type(field_values[field_name]) is dict:
                        # TODO: Dict is a special case, which we cannot check isinstance
                        # We need to check the type of the field
                        continue
                    if not isinstance(field_values[field_name], info["type"]):
                        raise JsonFieldError(
                            field_name,
                            info["type"],
                            f"Expected {info['type']}, got {type(field_values[field_name])}",
                        )
                except Exception as e:
                    raise JsonFieldError(field_name, info["type"], str(e))

        return cls(**field_values)


def is_optional_type(tp) -> bool:
    """Check if type hint is Optional[T]."""
    origin = get_origin(tp)
    args = get_args(tp)

    if origin is Union or (sys.version_info >= (3, 10) and origin is UnionType):
        return type(None) in args
    return False
