from collections.abc import Sequence
from dataclasses import is_dataclass, fields
from typing import Any, Dict, Type, TypeVar, Generic, get_origin, get_args, List

T = TypeVar('T')
V = TypeVar('V')

class JsonSerializable(Generic[T]):
    """Base class for JSON serializable types"""
    @classmethod
    def from_json(cls: Type[T], data: Dict[Any, Any]|Sequence[Any]) -> T:
        return JsonCodec.from_json(data, cls)
    
    def to_json(self) -> Dict[Any, Any]:
        return JsonCodec.to_json(self)

class JsonCodec:
    @staticmethod
    def to_json(obj: Any) -> Any:
        """
        Encode an object to JSON.

        Args:
        obj: The object to encode.

        Returns:
        The encoded JSON object.
        """
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        
        # If object has custom to_json method, use it
        if hasattr(obj, 'to_json') and callable(obj.to_json):
            return obj.to_json()
            
        # Handle sequences
        if isinstance(obj, list):
            return [JsonCodec.to_json(item) for item in obj]
            
        # Handle dataclasses
        if is_dataclass(obj):
            return {
                field.name: JsonCodec.to_json(getattr(obj, field.name))
                for field in fields(obj)
            }
            
        return str(obj)

    @staticmethod
    def from_json(data: Any, target_type: Type[V]) -> V:
        """
        Decode JSON data into a target type.
        
        Args:
        data: This can take either a dictionary or a sequence of values. Values within 
            are expected to be JsonSerializable. 
        target_type: The type to decode the data into.

        Returns:
            The decoded value wrapped in the target type.
        """
            
        # Handle basic types
        if target_type in (str, int, float, bool):
            return data  # type: ignore
        
        # Handle dataclasses
        if is_dataclass(target_type):
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict for {target_type.__name__}, got {type(data)}")
            
            field_values = {}
            for field in fields(target_type):
                field_name = field.name
                if field_name in data:
                    field_values[field_name] = JsonCodec.from_json(data[field_name], field.type) # type: ignore
                else:
                    # Check by converting _ to -, if still not found, raise error
                    if field_name.replace("_", "-") in data:
                        field_values[field_name] = JsonCodec.from_json(data[field_name.replace("_", "-")], field.type) # type: ignore
                    else:
                        raise ValueError(f"Missing field {field_name} for {target_type.__name__}")
                    
            return target_type(**field_values)  # type: ignore
        else:
            # Handle generic types
            try:
                origin = get_all_subclasses(target_type)
                if origin is not None and Sequence in origin:
                    value = None
                    try:
                        value = target_type(data)
                    except Exception as e:
                        value = target_type([JsonCodec.from_json(item, target_type._element_type) for item in data])  # type: ignore
                    if value is None:
                        raise ValueError(f"Unable to parse {target_type.__name__} from {data}")
                    return value
                else:
                    raise ValueError(f"Subclass of {target_type.__name__} is not supported for JSON deserialization")

            except Exception as e:
                # If they have a custom from_json method, use it
                try:
                    return target_type(data)
                except Exception as e:
                    try:
                        return target_type.from_json(data)
                    except Exception as e:
                        raise ValueError(f"Unsupported type for JSON deserialization: {target_type}. Full error: {e}") from e

def json_serializable(cls: Type[T]) -> Type[T]:
    """Decorator to make a dataclass JSON serializable"""
    if not is_dataclass(cls):
        raise TypeError("json_serializable can only be applied to dataclasses")
    
    # Add JsonSerializable as a base class
    if JsonSerializable not in cls.__bases__:
        cls.__bases__ = (JsonSerializable,) + cls.__bases__
    
    return cls


def get_all_subclasses(cls: Type[T]) -> List[Type[T]]:
    """Get all subclasses of a class"""
    all_subclasses = []
    for subclass in cls.__mro__:
        all_subclasses.append(subclass)
    return all_subclasses

