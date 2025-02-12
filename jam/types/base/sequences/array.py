from typing import Generic, Sequence, Tuple, Type, TypeVar, Union, Callable, Any

from jam.utils.codec.codable import Codable
from jam.utils.codec.codec import Codec
from jam.utils.codec.composite.arrays import ArrayCodec
from .base import BaseSequence

T = TypeVar('T', bound=Codable)

class Array(BaseSequence, Generic[T]):
    """
    Fixed-length array is an extension of the BaseSequence, to only allow fixed length arrays.
    
    The array has a fixed length, append, extend, pop, insert, remove, and clear methods are not supported.
    Elements can be:
    - Set/Updated at any index
    - Swapped with another element at any index
    - Get from any index
    """
    
    _length: int = 0
    def __init__(self, initial: Sequence[T] = [], codec: Codec[T] | None = None):
        """
        Initialize array.
        
        Args:
            initial: Required initial values
        Raises:
            TypeError: If elements are not all of the same Codable type
            ValueError: If initial values don't match fixed length
        """
        if len(initial) != self._length:
            raise ValueError(f"Array: Initial values of length {len(initial)} must have length {self._length}")
        
        if codec is None:
            codec = ArrayCodec(self._length)
        
        super().__init__(initial=initial, codec=codec)

    def __setitem__(self, index: Union[int, slice], value: Union[T, Sequence[T]]) -> None:
        """Set item at index or slice."""
        if isinstance(index, slice):
            # Get slice indices
            start, stop, step = index.indices(self._length)
            # Calculate length of slice
            slice_len = len(range(start, stop, step))
            
            # If value is a single item, repeat it
            if not isinstance(value, Sequence):
                value = [value] * slice_len

            # Validate slice length matches value length
            if len(value) != slice_len:
                raise ValueError(f"Slice length {slice_len} does not match value length {len(value)}")
            
            # Set each value in slice
            for i, v in zip(range(start, stop, step), value):
                self._validate_value(v)
                self.value[i] = v
                
        else:
            if not 0 <= index < self._length:
                raise IndexError(f"Array: Index {index} out of range")
            self._validate_value(value)
            self.value[index] = value

    def append(self, value: T) -> None:
        raise ValueError("Cannot append to fixed-length array")

    def pop(self, index: int = -1) -> T:
        raise ValueError("Cannot pop from fixed-length array")

    def insert(self, index: int, value: T) -> None:
        raise ValueError("Cannot insert into fixed-length array")

    def remove(self, value: T) -> None:
        raise ValueError("Cannot remove from fixed-length array")

    def clear(self) -> None:
        raise ValueError("Cannot clear fixed-length array")

    def extend(self, values: Sequence[T]) -> None:
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
        cls._element_type = element_type  
        cls._length = length
        
        @staticmethod
        def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
            value, size = ArrayCodec.decode_from(length, element_type, buffer, offset)
            return cls(value), size
        
        cls.decode_from = decode_from
        
        return cls

    return decorator