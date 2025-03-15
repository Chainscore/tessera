"""JSON decorators."""

from dataclasses import dataclass, is_dataclass
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")

def with_json_metadata(**field_metadata: Dict[str, Any]):
    """Add JSON metadata to multiple fields."""

    def decorator(cls: Type[T]) -> Type[T]:
        if not is_dataclass(cls):
            cls = dataclass(cls)

        cls.metadata = {}

        for field_name, metadata in field_metadata.items():
            field_meta = {}
            if "name" in metadata:
                field_meta["json_name"] = metadata["name"]
            if metadata.get("skip_if_none", False):
                field_meta["skip_if_none"] = True
            if metadata.get("default", None):
                field_meta["default"] = metadata["default"]
            if field_name in cls.__dataclass_fields__:
                cls.metadata[field_name] = field_meta
            else:
                raise ValueError(f"Field '{field_name}' not found in dataclass")
        return cls

    return decorator
