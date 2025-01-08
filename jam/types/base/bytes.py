from dataclasses import dataclass
from typing import Any, Optional, Tuple, Union, cast

from jam.utils.codec.base import Codable
from jam.utils.codec.primitives.bytes import BytesCodec

@dataclass
class Bytes(Codable):
    """Variable-length byte sequence type."""
    value: bytes

    def __init__(self, data: Union[bytes, str, int]):
        """
        Initialize a byte sequence.
        
        Args:
            data: Input data, can be:
                - bytes: Used directly
                - str: Interpreted as hex string (with optional 0x prefix)
                - int: Converted to single byte
        """
        if isinstance(data, str):
            if data.startswith("0x"):
                value = bytes.fromhex(data[2:])
            else:
                value = bytes.fromhex(data)
        elif isinstance(data, int):
            value = bytes([data])
        else:
            value = data
            
        super().__init__(codec=BytesCodec())
        self.value = value

    def __len__(self) -> int:
        return len(self.value)

    def __bytes__(self) -> bytes:
        return self.value
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Bytes):
            return self.value == other.value
        elif isinstance(other, (bytes, bytearray)):
            return self.value == other
        return False
    
    def __repr__(self) -> str:
        return f"Bytes(0x{self.value.hex()})"
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple['Bytes', int]:
        value, size = BytesCodec.decode_from(buffer, offset)
        return Bytes(value), size
