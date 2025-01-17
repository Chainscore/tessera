from typing import Callable, Sequence, Tuple, Type, TypeVar, Union

from jam.types.base.bit import Bit
from jam.utils.codec.composite.bit_sequences import BitSequenceCodec

from .base import BaseSequence
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.vectors import VectorCodec

T = TypeVar('T', bound=Codable)

class Vector(BaseSequence[T]):
    """
    Dynamic array implementation that supports codec operations.
    
    The vector grows dynamically as elements are added. All standard sequence
    operations are supported. All elements must be instances of the same Codable type.
    """
    
    def __init__(self, initial: Sequence[T] = []):
        if self._element_type is Bit:
            # Variable length bit sequence
            super().__init__(initial, codec=BitSequenceCodec(None))
        else:
            super().__init__(initial, codec=VectorCodec())

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