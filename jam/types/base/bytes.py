"""Bytes type for the JAM protocol."""
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from jam.utils.codec.base import Codable

@dataclass
class Bytes(Codable):
    """Variable-length byte sequence type."""
    data: bytes

    def __init__(self, data: bytes):
        self.data = data

    def __len__(self) -> int:
        return len(self.data)

    def __bytes__(self) -> bytes:
        return self.data

    def encode_size(self) -> int:
        return len(self.data)

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        buffer[offset:offset + len(self.data)] = self.data
        return len(self.data)

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        # For simplicity, assume remaining buffer is the byte sequence
        data = buffer[offset:]
        return Bytes(data), len(data)

    @staticmethod
    def decode_with_length(buffer: bytes, offset: int = 0, length: Optional[int] = None) -> Tuple[Any, int]:
        """Decode bytes with a known length."""
        if length is None:
            return Bytes.decode_from(buffer, offset)
        data = buffer[offset:offset + length]
        return Bytes(data), length 