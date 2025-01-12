from typing import Generic, List, Optional, Sequence, Type, TypeVar, Union
from jam.utils.codec.base import Codec, Codable

T = TypeVar('T', bound=Codable)

class BaseSequence(Codable[Sequence[T]], Generic[T], Sequence[T]):
    """
    Base class for sequence types (Array and Vector).
    
    Provides common functionality for sequence types that support codec operations.
    All elements must be instances of the same Codable type.
    """
    
    _element_type: Optional[Type[T]] = None
    _data: List[T] = []
    
    def __len__(self) -> int:
        """Get number of elements."""
        return len(self._data)

    def __getitem__(self, index: Union[int, slice]) -> Union[T, Sequence[T]]:
        """Get item at index."""
        return self._data[index]

    def __iter__(self):
        """Iterate over elements."""
        return iter(self._data)

    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.__class__.__name__}({self._data!r})"

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
            return (self._element_type == other._element_type and 
                   self._data == other._data)
        if isinstance(other, list) or isinstance(other, tuple):
            return all(x == y for x, y in zip(self._data, other))
        return False

    @property
    def value(self) -> Sequence[T]:
        """Get the value for encoding."""
        return self._data

    @property
    def element_type(self) -> Optional[Type[T]]:
        """Get the type of elements in this sequence."""
        return self._element_type