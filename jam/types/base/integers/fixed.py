from typing import Callable, Union, Any, Tuple, TypeVar, Type
from jam.utils.codec.codable import Codable
from jam.utils.codec.primitives.integers import IntegerCodec
from .base import BaseInteger

T = TypeVar('T', bound='BaseInteger')

class FixedInt(BaseInteger, Codable):
    """Fixed-width integer type."""
    byte_size: int = 0
    
    def __init__(self, value: Union[int, 'BaseInteger']):
        super().__init__(value)
        self._validate(self.value)
        self.codec = IntegerCodec(self.byte_size)
        
    def _validate(self, value: int) -> None:
        """Validate the integer value is within bounds."""
        if self.byte_size > 0:  # Fixed width
            max_value = (1 << (8 * self.byte_size)) - 1
            if not 0 <= value <= max_value:
                raise ValueError(f"Value must be between 0 and {max_value}, got {value}")

    def to_json(self) -> int:
        """Convert integer to JSON value.
        
        Returns:
            Integer value
        """
        return self.value

    @classmethod
    def from_json(cls, data: int) -> 'FixedInt':
        """Create integer from JSON value.
        
        Args:
            data: Integer value
            
        Returns:
            New FixedInt instance
            
        Raises:
            TypeError: If data is not an integer
            ValueError: If value is out of range
        """
        if not isinstance(data, int):
            raise TypeError("Value must be an integer")
        return cls(data)

def decodable_int(byte_size: int) -> Callable[[Type[FixedInt]], Type[FixedInt]]:
    """Decorator to make a class decodable as an integer."""
    def decorator(cls: Type[FixedInt]) -> Type[FixedInt]:
        cls.byte_size = byte_size
        
        @staticmethod
        def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
            value, size = IntegerCodec(byte_size).decode_from(byte_size, buffer, offset)
            return cls(value), size
            
        cls.decode_from = decode_from
        return cls
    return decorator

@decodable_int(1)
class U8(FixedInt): ...

@decodable_int(2)
class U16(FixedInt): ...

@decodable_int(4)
class U32(FixedInt): ...

@decodable_int(8)
class U64(FixedInt): ...

@decodable_int(16)
class U128(FixedInt): ...

@decodable_int(32)
class U256(FixedInt): ...

@decodable_int(64)
class U512(FixedInt): ...
