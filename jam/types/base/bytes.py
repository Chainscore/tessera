"""Bytes type for the JAM protocol."""
from dataclasses import dataclass
from typing import Any, Optional, Tuple, Union

from jam.utils.codec.base import Codable
from jam.utils.codec.primitives.integers import GeneralCodec

@dataclass
class Bytes(Codable):
    """Variable-length byte sequence type."""
    data: bytes

    def __init__(self, data: Union[bytes, str, int]):
        if isinstance(data, str):
            if data.startswith("0x"):
                self.data = bytes.fromhex(data[2:])
            else:
                self.data = bytes.fromhex(data)
        elif isinstance(data, int):
            self.data = bytes([data])
        else:
            self.data = data

    def __len__(self) -> int:
        return len(self.data)

    def __bytes__(self) -> bytes:
        return self.data

    def encode_size(self) -> int:
        return GeneralCodec().encode_size(len(self.data)) + len(self.data)

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        size = GeneralCodec().encode_into(len(self.data), buffer, offset)   
        buffer[offset + size:offset + size + len(self.data)] = self.data
        return size + len(self.data)

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        # For simplicity, assume remaining buffer is the byte sequence
        length, size = GeneralCodec().decode_from(buffer, offset)
        data = buffer[offset + size:offset + size + length]
        return Bytes(data), size + length
    
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Bytes):
            return self.data == other.data
        return False
