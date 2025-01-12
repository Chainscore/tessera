from typing import Type, Union, Any, Optional, List, Tuple, Dict, Callable, TypeVar, Generic

from jam.types.base.null import Null
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.choices import ChoiceCodec

T = TypeVar('T')

class Choice(Codable[T], Generic[T]):
    """
    A choice is a value that can be one of several possible types.
    
    A Choice represents a tagged union type that can hold a value of one of several
    possible Codable types. The actual type is determined by a tag byte during
    encoding/decoding.
    
    Examples:
        >>> from jam.types.base.boolean import Boolean
        >>> from jam.types.base.integers import U8
        >>> choice = Choice([Boolean, U8])
        >>> choice.set(Boolean(True))
        >>> encoded = choice.encode()
        >>> decoded, _ = Choice.decode_from([Boolean, U8], encoded)
        >>> decoded == Boolean(True)
        True
    """

    def __init__(self, types: List[Type[Codable[T]]], default: Optional[Codable[T]] = None):
        """
        Initialize Choice.
        
        Args:
            types: List of possible types for this choice
            default: Optional default value
            
        Raises:
            ValueError: If types list is empty
        """
        if len(types) == 0:
            raise ValueError("Choice must have at least one type")
            
        super().__init__(codec=ChoiceCodec(types))
        self.types = types
        self.value: Optional[Codable[T]] = None
        
        if default is not None:
            self.set(default)

    def set(self, value: Codable[T]) -> None:
        """
        Set the choice value.
        
        Args:
            value: Value to set. Must be instance of one of the allowed types.
            
        Raises:
            ValueError: If value type is not in allowed types list
        """
        if not isinstance(value, Codable):
            raise TypeError("Choice value must be Codable")
            
        if type(value) not in self.types:
            raise ValueError(f"Value type {type(value)} is not in allowed types: {self.types}")
            
        self.value = value

    def get(self) -> Optional[Codable[T]]:
        """
        Get the current value.
        
        Returns:
            Current value or None if not set
        """
        return self.value

    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        if not isinstance(other, Choice):
            return False
        return self.value == other.value

    def __repr__(self) -> str:
        """Get string representation."""
        return f"Choice({self.value!r})"

    @staticmethod
    def decode_from(
        types: List[Type[Codable[T]]], 
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> Tuple[Codable[T], int]:
        """
        Decode choice from buffer.
        
        Args:
            types: List of possible types for this choice
            buffer: Source buffer
            offset: Starting offset
            
        Returns:
            Tuple of (decoded value, bytes read)
            
        Raises:
            DecodeError: If buffer is invalid or too short
            ValueError: If types list is empty
        """
        if len(types) == 0:
            raise ValueError("Choice must have at least one type")
            
        return ChoiceCodec.decode_from(types, buffer, offset)