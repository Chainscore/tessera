from typing import Callable, Optional, Sequence, Tuple, Type, TypeVar, Union

from .base import BaseSequence
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.vectors import VectorCodec

T = TypeVar('T', bound=Codable)

class Vector(BaseSequence[T]):
    """
    Dynamic array implementation that supports codec operations.
    
    The vector grows dynamically as elements are added. All standard sequence
    operations are supported. All elements must be instances of the same Codable type.
    
    Examples:
        >>> from jam.types.base.integers import Int
        >>> vec = Vector([Int(1), Int(2), Int(3)])
        >>> assert len(vec) == 3
        >>> assert vec[0] == Int(1)
        >>> encoded = vec.encode()
        >>> decoded, _ = Vector.decode_from(Int, encoded)
        >>> assert decoded == vec
    """
    
    def __init__(self, initial: Sequence[T] = []):
        """
        Initialize vector.
        
        Args:
            initial: Optional initial values. All elements must be instances
                    of the same Codable type.
                    
        Raises:
            TypeError: If elements are not all of the same Codable type
        """
        super().__init__(codec=VectorCodec())
        self._data = list(initial)

    def __setitem__(self, index: int, value: T) -> None:
        """Set item at index."""
        if not 0 <= index < len(self._data):
            raise IndexError(f"Index {index} out of range")
            
        self._validate_value(value)
        self._data[index] = value

    def append(self, value: T) -> None:
        """
        Append value to end of vector.
        
        Args:
            value: Value to append. Must be instance of the same type as other elements.
            
        Raises:
            TypeError: If value is not of the correct type
        """
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
        """
        return self._data.pop(index)

    def insert(self, index: int, value: T) -> None:
        """
        Insert value at index.
        
        Args:
            index: Index to insert at
            value: Value to insert. Must be instance of the same type as other elements.
            
        Raises:
            TypeError: If value is not of the correct type
        """
        self._validate_value(value)
        self._data.insert(index, value)

    def remove(self, value: T) -> None:
        """
        Remove first occurrence of value.
        
        Args:
            value: Value to remove
            
        Raises:
            ValueError: If value not found
        """
        self._data.remove(value)

    def clear(self) -> None:
        """Clear all elements."""
        self._data.clear()
        self._element_type = None

    def count(self, value: T) -> int:
        """
        Return number of occurrences of value.
        
        Args:
            value: Value to count
            
        Returns:
            Number of occurrences
        """
        return self._data.count(value)

    def index(self, value: T, start: int = 0, stop: Optional[int] = None) -> int:
        """
        Return first index of value.
        
        Args:
            value: Value to find
            start: Start index for search
            stop: Stop index for search
            
        Returns:
            Index of value
            
        Raises:
            ValueError: If value not found
        """
        if stop is None:
            stop = len(self)
        return self._data.index(value, start, stop)

    def reverse(self) -> None:
        """Reverse the vector in place."""
        self._data.reverse()

    def extend(self, values: Sequence[T]) -> None:
        """
        Extend vector with values.
        
        Args:
            values: Values to add. Must all be instances of the same type as existing elements.
            
        Raises:
            TypeError: If values are not all of the correct type
        """
        for value in values:
            self.append(value)

    def __bytes__(self) -> bytes:
        # Combine bytes of all values in the vector
        return b''.join(bytes(value) for value in self._data)


def decodable_vector(element_type: Type[T]) -> Callable[[Type['Vector[T]']], Type['Vector[T]']]:
    """Decorator to make a class decodable as a vector."""
    def decorator(cls: Type['Vector[T]']) -> Type['Vector[T]']:
        
        @staticmethod
        def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple['Vector[T]', int]:
            if not issubclass(element_type, Codable):
                raise TypeError("Vector element type must be Codable")
            
            value, size = VectorCodec.decode_from(element_type, buffer, offset)
            return cls(value), size
        
        cls.decode_from = decode_from
        return cls
    return decorator
