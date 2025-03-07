"""JSON decorators."""

from dataclasses import dataclass, is_dataclass, field
from typing import Any, Dict, Type, TypeVar, Optional, get_type_hints
from .serde import JsonSerde

T = TypeVar("T")


def json_field(
    *,
    name: Optional[str] = None,
    skip_if_none: bool = False,
) -> Any:
    """Field decorator for JSON customization."""
    metadata = {}
    if name is not None:
        metadata["json_name"] = name
    if skip_if_none:
        metadata["skip_if_none"] = skip_if_none

    return field(metadata=metadata, default=None)


def json_serializable(cls: Type[T]) -> Type[T]:
    """Add JSON serialization to a class."""
    # If it's not a dataclass, make it one
    if not is_dataclass(cls):
        cls = dataclass(cls)

    # Create a new class that includes JsonSerde
    bases = cls.__bases__
    if JsonSerde not in cls.__mro__:
        bases = (JsonSerde,) + bases

    namespace = {
        "__module__": cls.__module__,
        "__qualname__": cls.__qualname__,
        "__annotations__": cls.__annotations__,
        "__doc__": cls.__doc__,
    }

    for name, attr in cls.__dict__.items():
        if name not in ("__dict__", "__weakref__"):
            namespace[name] = attr

    JsonSerializableClass = type(cls.__name__, bases, namespace)
    JsonSerializableClass.__json_type_hints__ = get_type_hints(cls)

    return JsonSerializableClass


def json_field_metadata(
    field_name: str,
    *,
    json_name: Optional[str] = None,
    skip_if_none: bool = False,
) -> Dict[str, Any]:
    """Create metadata for a JSON field."""
    metadata = {}
    if json_name is not None:
        metadata["json_name"] = json_name
    if skip_if_none:
        metadata["skip_if_none"] = skip_if_none
    return metadata


def with_json_metadata(**field_metadata: Dict[str, Any]):
    """Add JSON metadata to multiple fields."""

    def decorator(cls: Type[T]) -> Type[T]:
        if not is_dataclass(cls):
            cls = dataclass(cls)

        for field_name, metadata in field_metadata.items():
            field_meta = {}
            if "name" in metadata:
                field_meta["json_name"] = metadata["name"]
            if metadata.get("skip_if_none", False):
                field_meta["skip_if_none"] = True

            if field_name in cls.__dataclass_fields__:
                field_obj = cls.__dataclass_fields__[field_name]
                object.__setattr__(field_obj, "metadata", field_meta)
            else:
                raise ValueError(f"Field '{field_name}' not found in dataclass")

        return cls

    return decorator
