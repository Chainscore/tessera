from typing import Sequence, Tuple, Type, TypeVar, Union, Callable, Any

from jam.types.base.bit import Bit
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.arrays import ArrayCodec
from jam.utils.codec.composite.bit_sequences import BitSequenceCodec
from .base import BaseSequence

T = TypeVar('T', bound=Codable)

class Array(BaseSequence):
    """
    Fixed-length array is an extension of the BaseSequence, to only allow fixed length arrays.
    
    The array has a fixed length, append, extend, pop, insert, remove, and clear methods are not supported.
    Elements can be:
    - Set/Updated at any index
    - Swapped with another element at any index
    - Get from any index
    """
    
    _length: int = 0
    
    def __init__(self, initial: Sequence[T] = []):
        """
        Initialize array.
        
        Args:
            length: Fixed length of the array
            initial: Required initial values
        Raises:
            TypeError: If elements are not all of the same Codable type
            ValueError: If initial values don't match fixed length
        """
        if len(initial) != self._length:
            raise ValueError(f"Array: Initial values must have length {self._length}")
        
        if self._element_type is Bit:
            super().__init__(initial, codec=BitSequenceCodec(self._length))
        else:
            super().__init__(initial, codec=ArrayCodec(self._length))

    def __setitem__(self, index: int, value: T) -> None:
        """Set item at index."""
        if not 0 <= index < self._length:
            raise IndexError(f"Array: Index {index} out of range")
        super().__setitem__(index, value)

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
        cls._element_type = element_type  # type: ignore
        cls._length = length
        
        @staticmethod
        def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
            value, size = ArrayCodec.decode_from(length, element_type, buffer, offset)
            return cls(value), size
        
        cls.decode_from = decode_from
        
        return cls

    return decorator