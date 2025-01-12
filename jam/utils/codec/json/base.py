"""Base classes for JSON serialization."""
from typing import Any, Dict, TypeVar, Generic, Type, ClassVar, Protocol, runtime_checkable
from dataclasses import is_dataclass

T = TypeVar('T')

@runtime_checkable
class JsonSerializable(Protocol):
    """Protocol defining JSON serialization interface."""
    @classmethod
    def from_json(cls: Type[T], data: Dict[str, Any]) -> T: ...
    def to_json(self) -> Dict[str, Any]: ...

class JsonBase(Generic[T]):
    """Base class for JSON serializable types.
    
    This class provides default implementations for JSON serialization
    and deserialization. Classes that inherit from this base should be
    dataclasses and implement any custom serialization logic by overriding
    these methods.
    
    Example:
        @dataclass
        class MyType(JsonBase['MyType']):
            field1: int
            field2: str
    """
    
    @classmethod
    def from_json(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create an instance from a JSON dictionary.
        
        Args:
            data: Dictionary containing the serialized data
            
        Returns:
            An instance of the class
            
        Raises:
            ValueError: If the data is invalid or missing required fields
            TypeError: If the data contains invalid types
        """
        from jam.utils.codec.json import JsonCodec
        return JsonCodec.from_json(data, cls)
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the instance to a JSON dictionary.
        
        Returns:
            Dictionary containing the serialized data
        """
        from jam.utils.codec.json import JsonCodec
        return JsonCodec.to_json(self)