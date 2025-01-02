"""
Array codec implementation for JAM specification.

Arrays are encoded by concatenating their encoded elements with no length prefix.
The length is known at compile-time in Rust; in Python we enforce it at runtime.
Maximum array size is 1000 elements as per specification.
"""

from typing import Iterable, List, Tuple, Union, Sequence

from ..base import Codable, Codec, EncodeError, DecodeError
from ..utils import check_buffer_size

class ArrayCodec(Codec[Sequence[Codable]]):
    """
    Codec for fixed-length arrays/sequences.
    
    Arrays are encoded by concatenating their encoded elements in order.
    The length is fixed and known at encoding/decoding time.
    """
    
    MAX_SIZE = 1000
    length: int
    
    def __init__(self, length: int):
        if length > self.MAX_SIZE:
            raise ValueError(
                f"Array length {length} exceeds maximum allowed size {self.MAX_SIZE}"
            )
        if length < 0:
            raise ValueError(f"Array length cannot be negative: {length}")
            
        self.length = length
            
    def encode_size(self, value: Sequence[Codable]) -> int:
        if len(value) != self.length:
            raise EncodeError(
                self.length, len(value),
                f"Array length mismatch: expected {self.length}, got {len(value)}"
            )
        if not isinstance(value, Iterable):
            raise EncodeError(
                0, 0,
                f"Expected Iterable, got {type(value)}"
            )
        size = 0
        for item in value:
            if not isinstance(item, Codable):
                raise EncodeError(
                    0, 0,
                    f"Expected Codable, got {type(item)}"
                )
            size += item.encode_size()
            
        return size
        
    def encode_into(self, value: Sequence[Codable], buffer: bytearray, offset: int = 0) -> int:
        if len(value) != self.length:
            raise EncodeError(
                self.length, len(value),
                f"Array length mismatch: expected {self.length}, got {len(value)}"
            )
            
        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)
        
        current_offset = offset
        for item in value:
            written = item.encode_into(buffer, current_offset)
            current_offset += written
            
        return current_offset - offset
        
    @staticmethod
    def decode_from(length: int, codable_class: type[Codable], buffer: Union[bytes, bytearray, memoryview], 
                   offset: int = 0) -> Tuple[List, int]:
        result = []
        current_offset = offset
        bytes_read = 0
        
        try:
            for _ in range(length):
                item, size = codable_class.decode_from(buffer, current_offset)
                result.append(item)
                current_offset += size
                bytes_read += size
        except DecodeError as e:
            raise DecodeError(
                0, 0,
                f"Failed to decode array element {len(result)}: {str(e)}"
            )
            
        return result, bytes_read