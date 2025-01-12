from dataclasses import is_dataclass, fields
from typing import Any, Dict, Type, TypeVar, Generic, get_origin, get_args, Union, Optional, List, Protocol, runtime_checkable
from jam.types.base.option import Option
from jam.types.base.null import Null
from .types import encode_bytes, decode_bytes, encode_integer, decode_integer

T = TypeVar('T')
V = TypeVar('V')

@runtime_checkable
class JsonSerializableProtocol(Protocol):
    """Protocol for JSON serializable types"""
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Any: ...
    def to_json(self) -> Dict[str, Any]: ...

class JsonSerializable(Generic[T]):
    """Base class for JSON serializable types"""
    @classmethod
    def from_json(cls: Type[T], data: Dict[str, Any]) -> T:
        return JsonCodec.from_json(data, cls)
    
    def to_json(self) -> Dict[str, Any]:
        return JsonCodec.to_json(self)

class JsonCodec:
    @staticmethod
    def to_json(obj: Any) -> Any:
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, Option):
            if isinstance(obj.value, Null):
                return None
            return JsonCodec.to_json(obj.value)
        if isinstance(obj, list):
            return [JsonCodec.to_json(item) for item in obj]
        if is_dataclass(obj):
            return {
                field.name: JsonCodec.to_json(getattr(obj, field.name))
                for field in fields(obj)
            }
        if hasattr(obj, 'value') and isinstance(obj.value, int):
            return encode_integer(obj)
        if hasattr(obj, 'to_bytes') or hasattr(obj, 'value'):
            return encode_bytes(obj)
        return str(obj)

    @staticmethod
    def from_json(data: Any, target_type: Type[V]) -> V:
        # Handle None values
        if data is None:
            origin = get_origin(target_type)
            if origin is Option or origin is Optional:
                value_type = get_args(target_type)[0]
                return Option[value_type](Null())  # type: ignore
            return None  # type: ignore
            
        # Handle basic types
        if target_type in (str, int, float, bool):
            return data  # type: ignore
            
        # Handle dataclasses
        if is_dataclass(target_type):
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict for {target_type.__name__}, got {type(data)}")
                
            field_values = {}
            for field in fields(target_type):
                if field.name in data:
                    field_values[field.name] = JsonCodec.from_json(data[field.name], field.type) # type: ignore
                else:
                    raise ValueError(f"Missing field {field.name} for {target_type.__name__}")
                    
            return target_type(**field_values)  # type: ignore
            
        # Handle generic types
        origin = get_origin(target_type)
        if origin is not None:
            if origin is list or origin is List:
                item_type = get_args(target_type)[0]
                return [JsonCodec.from_json(item, item_type) for item in data]  # type: ignore
            if origin is Option:
                value_type = get_args(target_type)[0]
                if data is None:
                    return Option[value_type](Null())  # type: ignore
                return Option[value_type](JsonCodec.from_json(data, value_type))  # type: ignore
            
        # Handle integer-like types
        if hasattr(target_type, 'value') and hasattr(target_type, 'byte_size'):
            return decode_integer(data, target_type)  # type: ignore
            
        # Handle bytes-like types
        if hasattr(target_type, 'to_bytes') or hasattr(target_type, 'value'):
            return decode_bytes(data, target_type)  # type: ignore
            
        raise ValueError(f"Unsupported type: {target_type}")

def json_serializable(cls: Type[T]) -> Type[T]:
    """Decorator to make a dataclass JSON serializable"""
    if not is_dataclass(cls):
        raise TypeError("json_serializable can only be applied to dataclasses")
    
    # Add JsonSerializable as a base class
    if JsonSerializable not in cls.__bases__:
        cls.__bases__ = (JsonSerializable,) + cls.__bases__
    
    return cls
