"""Cryptographic types for the JAM protocol."""
from typing import NewType, Self, Tuple, Union

from jam.utils.codec.base import Codable

class ByteArray(Codable, bytes):
    """Fixed-width byte array type."""
    size: int = 0

    def __init__(self, value: Union[bytes, bytearray, memoryview]):
        if len(value) != self.size:
            raise ValueError(f"Expected {self.size} bytes, got {len(value)}")

    def __new__(cls, value: Union[bytes, bytearray, memoryview]):
        if len(value) != cls.size:
            raise ValueError(f"Expected {cls.size} bytes, got {len(value)}")
        return super().__new__(cls, value)
    
    def encode_size(self) -> int:
        return self.size
    
    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        buffer[offset:offset + self.size] = self
        return self.size
    
    @staticmethod
    def decode_from(size: int, buffer: bytes, offset: int = 0):
        return buffer[offset:offset + size], size

class ByteArray8(ByteArray):
    """8-bit byte array type."""
    size: int = 8

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0):
        value, size = ByteArray.decode_from(8, buffer, offset)
        return ByteArray8(value), size

class ByteArray16(ByteArray):
    """16-bit byte array type."""
    size: int = 16

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0):
        value, size = ByteArray.decode_from(16, buffer, offset)
        return ByteArray16(value), size

class ByteArray32(ByteArray):
    """32-bit byte array type."""
    size: int = 32

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0):
        value, size = ByteArray.decode_from(32, buffer, offset)
        return ByteArray32(value), size

class ByteArray64(ByteArray):
    """64-bit byte array type."""
    size: int = 64

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0):
        value, size = ByteArray.decode_from(64, buffer, offset)
        return ByteArray64(value), size

class ByteArray96(ByteArray):
    """96-bit byte array type."""
    size: int = 96

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0):
        value, size = ByteArray.decode_from(96, buffer, offset)
        return ByteArray96(value), size

class ByteArray128(ByteArray):
    """128-bit byte array type."""
    size: int = 128

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0):
        value, size = ByteArray.decode_from(128, buffer, offset)
        return ByteArray128(value), size

class ByteArray144(ByteArray):
    """144-bit byte array type."""
    size: int = 144

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0):
        value, size = ByteArray.decode_from(144, buffer, offset)
        return ByteArray144(value), size

class ByteArray256(ByteArray):
    """256-bit byte array type."""
    size: int = 256

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0):
        value, size = ByteArray.decode_from(256, buffer, offset)
        return ByteArray256(value), size

class ByteArray784(ByteArray):
    """784-bit byte array type."""
    size: int = 784

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0):
        value, size = ByteArray.decode_from(784, buffer, offset)
        return ByteArray784(value), size
