from types import NoneType
from typing import Any, Optional, Tuple, Type, TypeVar, Union, Generic, cast

from jam.types.base.null import Null
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.choices import ChoiceCodec

T = TypeVar('T', bound=Codable)

class Option(Codable[T], Generic[T]):
    """
    An optional value that can be either None or a value of type T.
    
    An Option represents a value that may or may not be present. It is encoded
    using a choice between Null and the value type T.
    
    Examples:
        >>> from jam.types.base.string import String
        >>> opt = Option(String)  # Empty option
        >>> assert opt.get() is None
        >>> opt.set(String("hello"))  # Set a value
        >>> assert opt.get() == String("hello")
        >>> encoded = opt.encode()
        >>> decoded, _ = Option.decode_from(String, encoded)
        >>> assert decoded == opt
    """
    
    def __init__(self, type: Type[T], value: Optional[T] = None):
        """
        Initialize Option.
        
        Args:
            type: The type of value this option can hold
            value: Optional initial value
            
        Raises:
            TypeError: If type is not Codable
        """
        if not issubclass(type, Codable):
            raise TypeError("Option type must be Codable")
            
        super().__init__(codec=ChoiceCodec([Null, type]))
        self.type = type
        self._value: Optional[T] = None
        
        if value is not None:
            self.set(value)
    
    def set(self, value: T) -> None:
        """
        Set the option value.
        
        Args:
            value: Value to set. Must be instance of the option's type.
            
        Raises:
            TypeError: If value is not of the correct type
        """
        if not isinstance(value, self.type):
            raise TypeError(f"Value must be instance of {self.type}")
            
        self._value = value
    
    def get(self) -> Optional[T]:
        """
        Get the current value.
        
        Returns:
            Current value or None if not set
        """
        return self._value
    
    def __repr__(self) -> str:
        """Get string representation."""
        return f"Option({self._value!r})"
    
    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        if isinstance(other, Option):
            return self.type == other.type and self._value == other._value
        if isinstance(other, NoneType):
            return self._value is None
        if isinstance(other, self.type):
            return self._value == other
        return self._value == other
    
    @property
    def value(self) -> Codable:
        """Get the value for encoding."""
        return Null() if self._value is None else self._value
    
    @staticmethod
    def decode_from(
        type: Type[T],
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> Tuple['Option[T]', int]:
        """
        Decode option from buffer.
        
        Args:
            type: The type of value this option can hold
            buffer: Source buffer
            offset: Starting offset
            
        Returns:
            Tuple of (decoded option, bytes read)
            
        Raises:
            DecodeError: If buffer is invalid or too short
            TypeError: If type is not Codable
        """
        if not issubclass(type, Codable):
            raise TypeError("Option type must be Codable")
            
        value, size = ChoiceCodec.decode_from([Null, type], buffer, offset)
        if isinstance(value, Null):
            return cast(Option[T], Option(type)), size
        return cast(Option[T], Option(type, cast(T, value))), size
