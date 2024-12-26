"""Integer types"""
from decimal import Decimal
from typing import Tuple

from jam.utils.codec.base import Codable
from jam.utils.codec.primitives.integers import IntegerCodec, u8_codec

# Simple integer types
class FixedInt(Codable, int):
    """Fixed-width integer type."""
    byte_size: int

    def __init__(self, value: int):
        self.codec = IntegerCodec(self.byte_size, int)

    def __new__(cls, value: int):
        max_value = 2**(8*cls.byte_size) - 1
        if not 0 <= value <= max_value:
            raise ValueError(
                f"{cls.__name__} value must be between 0 and {max_value}, got {value}"
            )
        instance = super().__new__(cls, value)
        return instance

class U8(FixedInt):
    """8-bit unsigned integer type."""
    byte_size = 1

    def __init__(self, value: int):
        super().__init__(value)

class U16(FixedInt):
    """16-bit unsigned integer type."""
    byte_size = 2

    def __init__(self, value: int):
        super().__init__(value)

class U32(FixedInt):
    """32-bit unsigned integer type."""
    byte_size = 4

    def __init__(self, value: int):
        super().__init__(value)

class U64(FixedInt):
    """64-bit unsigned integer type."""
    byte_size = 8

    def __init__(self, value: int):
        super().__init__(value)

class U128(FixedInt):
    """128-bit unsigned integer type."""
    byte_size = 16

    def __init__(self, value: int):
        super().__init__(value)

class U256(FixedInt):
    """256-bit unsigned integer type."""
    byte_size = 32

    def __init__(self, value: int):
        super().__init__(value)

class U512(FixedInt):
    """512-bit unsigned integer type."""
    byte_size = 64

    def __init__(self, value: int):
        super().__init__(value)


U8(1).encode()