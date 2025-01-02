"""Integer types"""
from typing import Union
from jam.utils.codec.base import Codable
from jam.utils.codec.primitives.integers import GeneralCodec, IntegerCodec

# General integer type
class Int(Codable, int):
    """General integer type."""
    
    def __init__(self, value: int):
        self.codec = GeneralCodec()

    def __new__(cls, value: int):
        max_value = 2**(8*8) - 1
        if not 0 <= value <= max_value:
            raise ValueError(
                f"{cls.__name__} value must be between 0 and {max_value}, got {value}"
            )
        instance = super().__new__(cls, value)
        return instance

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        return GeneralCodec.decode_from(buffer, offset)

# Fixed integer types
class FixedInt(Codable, int):
    """Fixed-width integer type."""
    byte_size: int

    def __init__(self, value: int):
        self.codec = IntegerCodec(self.byte_size)

    def __repr__(self):
        return f"U{8*self.byte_size}({int(self)})"

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
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        value, size = IntegerCodec.decode_from(U8.byte_size, buffer, offset)
        return U8(value), size

class U16(FixedInt):
    """16-bit unsigned integer type."""
    byte_size = 2

    def __init__(self, value: int):
        super().__init__(value)
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        value, size = IntegerCodec.decode_from(U16.byte_size, buffer, offset)
        return U16(value), size

class U32(FixedInt):
    """32-bit unsigned integer type."""
    byte_size = 4

    def __init__(self, value: int):
        super().__init__(value)
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        value, size = IntegerCodec.decode_from(U32.byte_size, buffer, offset)
        return U32(value), size

class U64(FixedInt):
    """64-bit unsigned integer type."""
    byte_size = 8

    def __init__(self, value: int):
        super().__init__(value)
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        value, size = IntegerCodec.decode_from(U64.byte_size, buffer, offset)
        return U64(value), size

class U128(FixedInt):
    """128-bit unsigned integer type."""
    byte_size = 16

    def __init__(self, value: int):
        super().__init__(value)
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        value, size = IntegerCodec.decode_from(U128.byte_size, buffer, offset)
        return U128(value), size

class U256(FixedInt):
    """256-bit unsigned integer type."""
    byte_size = 32

    def __init__(self, value: int):
        super().__init__(value)
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        value, size = IntegerCodec.decode_from(U256.byte_size, buffer, offset)
        return U256(value), size

class U512(FixedInt):
    """512-bit unsigned integer type."""
    byte_size = 64

    def __init__(self, value: int):
        super().__init__(value)
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        value, size = IntegerCodec.decode_from(U512.byte_size, buffer, offset)
        return U512(value), size
