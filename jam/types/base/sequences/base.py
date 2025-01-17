from typing import List, Optional, Sequence, Type, TypeVar, Union
from jam.utils.codec.base import Codable, Codec

T = TypeVar("T", bound=Codable)

class BaseSequence(Codable[Sequence[T]]):
    """
    Base class for sequence types.

    Provides common functionality for sequence types that support codec operations.
    All elements must be instances of the same Codable type.
    """

    _element_type: Optional[Type[T]] = None
    value: List[T]

    def __init__(self, initial: Sequence[T] = [], codec: Optional[Codec] = None):
        """
        Initialize sequence.
        
        Args:
            initial: Initial values
            codec: Optional codec
        """
        # Make sure initial values are all of the same type
        for value in initial:
            self.validate_value(value)
        self._codec = codec
        self.value = initial

    def validate_value(self, value: T) -> None:
        """Validate that a value is of the correct type."""
        if not isinstance(value, self._element_type):
            raise TypeError(f"Value must be instance of {self._element_type}")

    def __len__(self) -> int:
        """Get number of elements."""
        return len(self.value)

    def __getitem__(self, index: Union[int, slice]) -> Union[T, Sequence[T]]:
        """Get item at index."""
        return self.value[index]

    def __iter__(self):
        """Iterate over elements."""
        return iter(self.value)

    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.__class__.__name__}({self.value!r})"

    def _validate_value(self, value: T) -> None:
        """
        Validate that a value is of the correct type.

        Args:
            value: Value to validate

        Raises:
            TypeError: If value is not of the correct type
        """
        if not isinstance(value, Codable):
            raise TypeError("Elements must be Codable")

        if self._element_type is None:
            self._element_type = type(value)
        elif not isinstance(value, self._element_type):
            raise TypeError(f"Value must be instance of {self._element_type}")

    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        if isinstance(other, BaseSequence):
            if len(self) == 0 and len(other) == 0:
                return True
            return (
                self._element_type == other._element_type and self._data == other._data
            )
        if isinstance(other, list) or isinstance(other, tuple):
            return all(x == y for x, y in zip(self.value, other))
        return False

    @property
    def element_type(self) -> Optional[Type[T]]:
        """Get the type of elements in this sequence."""
        return self._element_type

    def __setitem__(self, index: int, value: T) -> None:
        """Set item at index."""
        if not 0 <= index < len(self.value):
            raise IndexError(f"Index {index} out of range")

        self._validate_value(value)
        self.value[index] = value

    def append(self, value: T) -> None:
        """
        Append value to end of vector.

        Args:
            value: Value to append. Must be instance of the same type as other elements.

        Raises:
            TypeError: If value is not of the correct type
        """
        self._validate_value(value)
        self.value.append(value)

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
        return self.value.pop(index)

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
        self.value.insert(index, value)

    def remove(self, value: T) -> None:
        """
        Remove first occurrence of value.

        Args:
            value: Value to remove

        Raises:
            ValueError: If value not found
        """
        self.value.remove(value)

    def clear(self) -> None:
        """Clear all elements."""
        self.value.clear()
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
        return b"".join(bytes(value) for value in self._data)