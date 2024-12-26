"""Cryptographic types for the JAM protocol."""
from typing import NewType, Self, Tuple

class ByteArray(bytes):
    """Fixed-width byte array type."""
    size: int = 0

    def __new__(cls, value: bytes):
        if len(value) != cls.size:
            raise ValueError(f"Expected {cls.size} bytes, got {len(value)}")
        return super().__new__(cls, value)
    
    def __init__(self, value: bytes):
        super().__init__()

    def encode_size(self) -> int:
        return self.size
    
    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        buffer[offset:offset + self.size] = self
        return self.size
    
    def decode_from(self, buffer: bytes, offset: int = 0) -> Tuple[Self, int]:
        return self.__class__(buffer[offset:offset + self.size]), self.size

class ByteArray8(ByteArray):
    """8-bit byte array type."""
    size: int = 8

class ByteArray16(ByteArray):
    """16-bit byte array type."""
    size: int = 16

class ByteArray32(ByteArray):
    """32-bit byte array type."""
    size: int = 32

class ByteArray64(ByteArray):
    """64-bit byte array type."""
    size: int = 64

class ByteArray96(ByteArray):
    """96-bit byte array type."""
    size: int = 96

class ByteArray128(ByteArray):
    """128-bit byte array type."""
    size: int = 128

class ByteArray144(ByteArray):
    """144-bit byte array type."""
    size: int = 144

class ByteArray256(ByteArray):
    """256-bit byte array type."""
    size: int = 256

class ByteArray784(ByteArray):
    """784-bit byte array type."""
    size: int = 784
