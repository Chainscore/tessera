"""Dynamic array (vector) implementation"""
from typing import Generic, List, Optional, Sequence, Tuple, Type, TypeVar, Union

from jam.types.base.integers import Int
from jam.utils.codec.base import Codec, Codable
from jam.utils.codec.composite.vectors import VectorCodec

T = TypeVar('T')

class Vector(Generic[T], Codable, Sequence[T]):
    """
    Dynamic array implementation that supports codec operations.
    
    The vector grows dynamically as elements are added. All standard sequence
    operations are supported.
    """
    
    def __init__(self, initial: Optional[Sequence[T]] = None):
        """
        Initialize vector.
        
        Args:
            initial: Optional initial values
        """
        self._data: List[T] = []
        self.codec = VectorCodec()

        if initial is not None:
            self._data.extend(initial)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, index: Union[int, slice]) -> Union[T, Sequence[T]]:
        return self._data[index]

    def __setitem__(self, index: int, value: T) -> None:
        if not 0 <= index < len(self._data):
            raise IndexError(f"Index {index} out of range")
        self._data[index] = value

    def __iter__(self):
        return iter(self._data)

    def __repr__(self) -> str:
        return f"Vector(data={self._data})"

    def append(self, value: T) -> None:
        """Append value to end of vector."""
        self._data.append(value)

    def pop(self, index: int = -1) -> T:
        """Remove and return item at index."""
        return self._data.pop(index)

    def insert(self, index: int, value: T) -> None:
        """Insert value at index."""
        self._data.insert(index, value)

    def remove(self, value: T) -> None:
        """Remove first occurrence of value."""
        self._data.remove(value)

    def clear(self) -> None:
        """Clear all elements."""
        self._data.clear()

    def count(self, value: T) -> int:
        """Return number of occurrences of value."""
        return self._data.count(value)

    def index(self, value: T, start: int = 0, stop: Optional[int] = None) -> int:
        """Return first index of value. Raises ValueError if not found."""
        if stop is None:
            stop = len(self)
        return self._data.index(value, start, stop)

    def reverse(self) -> None:
        """Reverse the vector in place."""
        self._data.reverse()

    def extend(self, values: Sequence[T]) -> None:
        """Extend vector with values."""
        self._data.extend(values)
        
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return False
        return self._data == other._data

    @staticmethod
    def decode_from(
        codable_class: Type[Codable[T]],
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> Tuple[Sequence[T], int]:
        value, size = VectorCodec.decode_from(codable_class, buffer, offset)
        return Vector(value), size
