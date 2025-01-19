from dataclasses import is_dataclass, fields
from typing import Any, Dict, Sequence, Type, TypeVar, Generic, get_origin, get_args, Optional, List, Protocol, runtime_checkable
from .types import encode_bytes, decode_bytes, encode_integer, decode_integer

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
        
        # Handle sequences
        if isinstance(obj, list):
            return [JsonCodec.to_json(item) for item in obj]
        
        # Handle Choice types (including Option)
        try:
            from jam.types.base.choices.choice import Choice
            if isinstance(obj, Choice):
                # For Option types, if value is None or Null, return None
                from jam.types.base.null import Null, Nullable
                if obj.value is None or isinstance(obj.value, Null):
                    return None
                # Otherwise serialize the value
                return JsonCodec.to_json(obj.value)
        except ImportError:
            pass
            
        # Handle dataclasses
        if is_dataclass(obj):
            return {
                field.name: JsonCodec.to_json(getattr(obj, field.name))
                for field in fields(obj)
            }
            
        # Handle objects with value attribute
        if hasattr(obj, 'value'):
            # Handle bit arrays and byte arrays
            if hasattr(obj, '_length'):  # BitArray or ByteArray
                return encode_bytes(obj)
            # Handle sequences
            if isinstance(obj.value, list):
                return [JsonCodec.to_json(item) for item in obj.value]
            # Handle integer types
            if isinstance(obj.value, int):
                return encode_integer(obj)
            # Handle boolean types
            if isinstance(obj.value, bool):
                return obj.value
            # Handle null type
            if obj.value is None:
                return None
            
        # Handle any remaining byte-like objects
        if hasattr(obj, 'to_bytes'):
            return encode_bytes(obj)
            
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
        # Handle None values
        if data is None:
            try:
                # Try to handle Option type with None value
                from jam.types.base.choices.option import Option
                if issubclass(target_type, Option):
                    from jam.types.base.null import Null
                    return target_type(Null())  # type: ignore
            except ImportError:
                pass
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
            if origin is list or origin is List or origin is Sequence:
                item_type = get_args(target_type)[0]
                return [JsonCodec.from_json(item, item_type) for item in data]  # type: ignore

        # Handle Choice types (including Option types)
        try:
            from jam.types.base.choices.choice import Choice
            if issubclass(target_type, Choice):
                # Get choices from the class
                choices = None
                for base in target_type.__mro__:
                    if hasattr(base, 'types'):
                        choices = base.types
                        break
                if choices is None:
                    raise ValueError(f"No types found for {target_type.__name__}")

                # Handle Option types specially
                from jam.types.base.null import Nullable
                if len(choices) == 2 and choices[0] == Nullable:
                    # This is an Option type
                    if data is None:
                        from jam.types.base.null import Null
                        return target_type(Null())  # type: ignore
                    else:
                        # Try to decode the value with the second type
                        value_type = choices[1]
                        try:
                            value = JsonCodec.from_json(data, value_type)
                            return target_type(value)  # type: ignore
                        except Exception as e:
                            raise ValueError(f"Failed to decode Option value: {e}")

                # For regular Choice types, try each possible type
                last_error = None
                for choice_type in choices:
                    try:
                        value = JsonCodec.from_json(data, choice_type)
                        return target_type(value)  # type: ignore
                    except (ValueError, TypeError) as e:
                        last_error = e
                        continue

                raise ValueError(f"No valid choice type found for {data} in {target_type.__name__}: {last_error}")
        except ImportError:
            pass

        # Handle BitArray types
        try:
            from jam.types.base.sequences.bytes.bit_array import BitArray
            if isinstance(data, str) and issubclass(target_type, BitArray):
                return target_type(data)  # type: ignore
        except ImportError:
            pass

        # Handle ByteArray types
        try:
            from jam.types.base.sequences.bytes.byte_array import ByteArray
            if isinstance(data, str) and issubclass(target_type, ByteArray):
                return target_type(data)  # type: ignore
        except ImportError:
            pass

        # Handle sequence types with _element_type
        if hasattr(target_type, '_element_type') and isinstance(data, list):
            sequence = target_type()
            element_type = target_type._element_type
            if element_type is not None:
                for item in data:
                    sequence.append(JsonCodec.from_json(item, element_type))
            return sequence  # type: ignore

        # Handle integer-like types
        if hasattr(target_type, 'value') and hasattr(target_type, 'byte_size'):
            return decode_integer(data, target_type)  # type: ignore
            
        # Handle other byte array types
        if hasattr(target_type, 'to_bytes') and isinstance(data, str):
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
