"""Fixed-size array implementation"""
from typing import Any, Generic, List, Optional, Sequence, Tuple, TypeVar, Union, overload

from jam.types.base.integers import Int
from jam.utils.codec.base import Codec, Codable
from jam.utils.codec.composite.arrays import ArrayCodec
from jam.utils.codec.primitives.integers import GeneralCodec

T = TypeVar('T')

class Array(Generic[T], Codable, Sequence[T]):
    """
    Fixed-size array implementation that maintains a constant size and supports codec operations.
    
    The array size is fixed at initialization and cannot be changed. All operations that would
    modify the size (append, extend, etc.) will raise ValueError if they would exceed the size.
    """
    
    def __init__(self, size: int, initial: Optional[Sequence[T]] = None):
        """
        Initialize fixed-size array.
        
        Args:
            size: Fixed size of the array
            codec: Codec for array elements
            initial: Optional initial values. Must not exceed size.
        """
        self.size = size
        self._data: List[Optional[T]] = []
        self.codec = ArrayCodec(size)

        if initial is not None:
            if len(initial) > size:
                raise ValueError(f"Initial data exceeds fixed size {size}")
            self._data.extend(initial)
            self._data.extend([None] * (size - len(initial)))
        else:
            self._data = [None] * size

    def __len__(self) -> int:
        return self.size

    @overload
    def __getitem__(self, index: int) -> T: ...
    
    @overload 
    def __getitem__(self, index: slice) -> Sequence[T]: ...
    
    def __getitem__(self, index: Union[int, slice]) -> Union[Optional[T], Sequence[Optional[T]]]:
        return self._data[index]

    def __setitem__(self, index: int, value: T) -> None:
        if not 0 <= index < self.size:
            raise IndexError(f"Index {index} out of range for size {self.size}")
        self._data[index] = value

    def __iter__(self):
        return iter(self._data)

    def __repr__(self) -> str:
        return f"Array(size={self.size}, data={self._data})"

    def append(self, value: T) -> None:
        """Append value if array is not full."""
        for i in range(self.size):
            if self._data[i] is None:
                self._data[i] = value
                return
        raise ValueError(f"Cannot append - array is full (size {self.size})")

    def pop(self, index: int = -1) -> Optional[T]:
        """Remove and return item at index, shifting remaining items left."""
        if index < 0:
            index = self.size + index
        if not 0 <= index < self.size:
            raise IndexError(f"Pop index {index} out of range for size {self.size}")
            
        value = self._data[index]
        # Shift remaining elements left
        for i in range(index, self.size - 1):
            self._data[i] = self._data[i + 1]
        self._data[-1] = None
        return value

    def insert(self, index: int, value: T) -> None:
        """Insert value at index if array is not full."""
        if self._data[-1] is not None:
            raise ValueError(f"Cannot insert - array is full (size {self.size})")
            
        # Shift elements right
        for i in range(self.size - 1, index, -1):
            self._data[i] = self._data[i - 1]
        self._data[index] = value

    def remove(self, value: T) -> None:
        """Remove first occurrence of value."""
        for i in range(self.size):
            if self._data[i] == value:
                self.pop(i)
                return
        raise ValueError(f"{value} not in array")

    def clear(self) -> None:
        """Clear array by setting all elements to None."""
        self._data = [None] * self.size

    def count(self, value: T) -> int:
        """Return number of occurrences of value."""
        return self._data.count(value)

    def index(self, value: T, start: int = 0, stop: Optional[int] = None) -> int:
        """Return first index of value. Raises ValueError if not found."""
        if stop is None:
            stop = self.size
        for i in range(start, stop):
            if self._data[i] == value:
                return i
        raise ValueError(f"{value} not in array")

    def reverse(self) -> None:
        """Reverse the array in place."""
        self._data.reverse()

    def extend(self, values: Sequence[T]) -> None:
        """Extend array with values."""
        for value in values:
            self.append(value)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Array):
            return False
        return self._data == other._data