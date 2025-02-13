from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar, Union
from jam.utils.codec.codable import Codable
from jam.utils.codec.codec import Codec
from jam.utils.json import JsonSerde
from jam.utils.json.serde import JsonDeserializationError

T = TypeVar("T", bound=Codable)

class BaseSequence(Codable[Sequence[T]], Sequence[T], JsonSerde, Generic[T]):
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
            self._validate_value(value)
        self.value = initial
        super().__init__(codec=codec)

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
        return f"{self.__class__.__name__}([{', '.join(f'{value!r}' for value in self.value)}])"

    def _validate_value(self, value: T) -> None:
        """
        Validate that a value is of the correct type.

        Args:
            value: Value to validate

        Raises:
            TypeError: If value is not of the correct type
        """
        if self._element_type is None:
            self._element_type = type(value)
        elif not str(type(value)) == str(self._element_type):
            raise TypeError(f"Value {value} must be instance of {self._element_type}. Debug: {str(type(value)) == str(self._element_type)}")

    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        if isinstance(other, BaseSequence):
            if len(self) == 0 and len(other) == 0:
                return True
            return (
                self._element_type == other._element_type and self.value == other.value
            )
        if isinstance(other, list) or isinstance(other, tuple):
            return all(x == y for x, y in zip(self.value, other))
        return False
    
    def __gt__(self, other: object) -> bool:
        """Compare for greater than."""
        if isinstance(other, BaseSequence):
            return self.value > other.value
        return False
    
    def __lt__(self, other: object) -> bool:
        """Compare for less than."""
        if isinstance(other, BaseSequence):
            return self.value < other.value
        return False
    
    def __ge__(self, other: object) -> bool:
        """Compare for greater than or equal to."""
        return self > other or self == other
    
    def __le__(self, other: object) -> bool:
        """Compare for less than or equal to."""
        if isinstance(other, BaseSequence):
            return self < other or self == other
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
        return self.value.count(value)

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
        return self.value.index(value, start, stop)

    def reverse(self) -> 'BaseSequence[T]':
        """Reverse the vector in place."""
        self.value.reverse()
        return self
    
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
        return b"".join(bytes(value) for value in self.value)

    def __add__(self, other: Union['BaseSequence[T]', Sequence[T]]) -> 'BaseSequence[T]':
        """Add two sequences together, returning a new sequence."""
        if isinstance(other, BaseSequence):
            other_values = other.value
        else:
            other_values = other
        new_sequence = self.__class__(self.value.copy())
        new_sequence.extend(other_values)
        return new_sequence

    def __iadd__(self, other: Union['BaseSequence[T]', Sequence[T]]) -> 'BaseSequence[T]':
        """In-place addition of sequences."""
        if isinstance(other, BaseSequence):
            self.extend(other.value)
        else:
            self.extend(other)
        return self

    def __mul__(self, n: int) -> 'BaseSequence[T]':
        """Multiply sequence by an integer, returning a new sequence."""
        if not isinstance(n, int):
            raise TypeError("Can only multiply sequence by an integer")
        new_sequence = self.__class__(self.value * n, codec=self.codec)
        return new_sequence

    def __imul__(self, n: int) -> 'BaseSequence[T]':
        """In-place multiplication of sequence."""
        if not isinstance(n, int):
            raise TypeError("Can only multiply sequence by an integer")
        self.value *= n
        return self

    def __contains__(self, item: T) -> bool:
        """Check if item is in sequence."""
        return item in self.value

    def copy(self) -> 'BaseSequence[T]':
        """Return a shallow copy of the sequence."""
        return self.__class__(self.value.copy(), codec=self.codec)

    def sort(self, *, key=None, reverse=False) -> None:
        """
        Sort the sequence in place.

        Args:
            key: Function of one argument that is used to extract a comparison key
            reverse: If True, sort in descending order
        """
        self.value.sort(key=key, reverse=reverse)

    def __reversed__(self):
        """Return a reverse iterator over the sequence."""
        return reversed(self.value)

    def __delitem__(self, index: Union[int, slice]) -> None:
        """Delete item at index."""
        del self.value[index]

    def __rmul__(self, n: int) -> 'BaseSequence[T]':
        """Right multiplication (n * sequence)."""
        return self.__mul__(n)
        
    def __hash__(self) -> None:
        """Sequences are mutable, so they should not be hashable."""
        from hashlib import blake2b
        return int.from_bytes(blake2b(bytes(self)).digest())
    
    def startswith(self, prefix: Sequence[T]) -> bool:
        """Check if sequence starts with prefix."""
        return self.value[:len(prefix)] == prefix
    
    def endswith(self, suffix: Sequence[T]) -> bool:
        """Check if sequence ends with suffix."""
        return self.value[-len(suffix):] == suffix
    
    @classmethod
    def from_json(cls, data: Any) -> 'BaseSequence[T]':
        """Deserialize from JSON."""
        if not isinstance(data, list):
            raise JsonDeserializationError(f"Expected list for {cls.__name__}, got {type(data)}")
        return cls([cls._element_type.from_json(item) for item in data])