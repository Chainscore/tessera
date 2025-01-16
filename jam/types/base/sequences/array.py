from typing import Sequence, Tuple, Type, TypeVar, Union, Callable, Any

from jam.utils.codec.base import Codable
from jam.utils.codec.composite.arrays import ArrayCodec
from .base import BaseSequence

T = TypeVar('T', bound=Codable)

class Array(BaseSequence[T]):
    """
    Fixed-length array implementation that supports codec operations.
    
    The array has a fixed length that is set at initialization. All elements
    must be instances of the same Codable type.
    """
    
    _length: int = 0
    _element_type: Type[T]
    
    def __init__(self, initial: Sequence[T] = []):
        """
        Initialize array.
        
        Args:
            length: Fixed length of the array
            initial: Optional initial values. Must match the fixed length.
                    All elements must be instances of the same Codable type.
                    
        Raises:
            TypeError: If elements are not all of the same Codable type
            ValueError: If initial values don't match fixed length
        """
        if len(initial) != self._length:
            raise ValueError(f"Array: Initial values must have length {self._length}")
        
        if len(initial) > 0 and not isinstance(initial[0], self._element_type):
            raise TypeError(f"Array: All elements in {type(initial[0])} must be instances of {self._element_type}")
        
        self._data = list(initial)
        
        super().__init__(codec=ArrayCodec(self._length))
        
    @property
    def length(self) -> int:
        """Get array length."""
        if self._length is None:
            raise ValueError("Array: Length not set")
        return self._length

    def __setitem__(self, index: int, value: T) -> None:
        """Set item at index."""
        if not 0 <= index < self.length:
            raise IndexError(f"Array: Index {index} out of range")
            
        self._validate_value(value)
        self._data[index] = value

    def append(self, value: T) -> None:
        """
        Append value to end of array.
        
        Args:
            value: Value to append. Must be instance of the same type as other elements.
            
        Raises:
            TypeError: If value is not of the correct type
            ValueError: If array is already at fixed length
        """
        if len(self._data) >= self.length:
            raise ValueError(f"Cannot append to array of fixed length {self.length}")
            
        self._validate_value(value)
        self._data.append(value)

    def pop(self, index: int = -1) -> T:
        """
        Remove and return item at index.
        
        Args:
            index: Index of item to remove
            
        Returns:
            Removed item
            
        Raises:
            IndexError: If index out of range
            ValueError: Array must maintain fixed length
        """
        raise ValueError("Cannot remove items from fixed-length array")

    def insert(self, index: int, value: T) -> None:
        """
        Insert value at index.
        
        Args:
            index: Index to insert at
            value: Value to insert
            
        Raises:
            ValueError: Array must maintain fixed length
        """
        raise ValueError("Cannot insert into fixed-length array")

    def remove(self, value: T) -> None:
        """
        Remove first occurrence of value.
        
        Args:
            value: Value to remove
            
        Raises:
            ValueError: Array must maintain fixed length
        """
        raise ValueError("Cannot remove from fixed-length array")

    def clear(self) -> None:
        """
        Clear all elements.
        
        Raises:
            ValueError: Array must maintain fixed length
        """
        raise ValueError("Cannot clear fixed-length array")

    def extend(self, values: Sequence[T]) -> None:
        """
        Extend array with values.
        
        Args:
            values: Values to add
            
        Raises:
            ValueError: Array must maintain fixed length
        """
        raise ValueError("Cannot extend fixed-length array")

def decodable_array(length: int, element_type: Type[T]) -> Callable[[Type[Any]], Type[Any]]:
    """
    Decorator that creates a fixed-length array type with a specific element type.
    
    This decorator configures the array class with:
    1. Fixed length
    2. Element type validation
    3. Custom decode_from implementation
    """
    def decorator(cls: Type[Array[T]]) -> Type[Array[T]]:
        cls._element_type = element_type  # type: ignore
        cls._length = length
        
        @staticmethod
        def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
            value, size = ArrayCodec.decode_from(length, element_type, buffer, offset)
            return cls(value), size
        
        cls.decode_from = decode_from
        
        return cls

    return decorator