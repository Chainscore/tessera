"""
Array codec implementation for JAM specification.

Arrays are encoded by concatenating their encoded elements with no length prefix.
The length is known at compile-time in Rust; in Python we enforce it at runtime.
Maximum array size is 1000 elements as per specification.
"""

from typing import List, Tuple, Union, Sequence

from ..base import Codec, EncodeError, DecodeError
from ..utils import check_buffer_size

class ArrayCodec(Codec[Sequence]):
    """
    Codec for fixed-length arrays/sequences.
    
    Arrays are encoded by concatenating their encoded elements in order.
    The length is fixed and known at encoding/decoding time.
    """
    
    MAX_SIZE = 1000
    
    def __init__(self, length: int, element_codec: Codec):
        if length > self.MAX_SIZE:
            raise ValueError(
                f"Array length {length} exceeds maximum allowed size {self.MAX_SIZE}"
            )
        if length < 0:
            raise ValueError(f"Array length cannot be negative: {length}")
            
        self.length = length
        self.element_codec = element_codec
            
    def encode_size(self, value: Sequence) -> int:
        if len(value) != self.length:
            raise EncodeError(
                self.length, len(value),
                f"Array length mismatch: expected {self.length}, got {len(value)}"
            )
        
        size = 0
        for item in value:
            size += self.element_codec.encode_size(item)
            
        return size
        
    def encode_into(self, value: Sequence, buffer: bytearray, offset: int = 0) -> int:
        if len(value) != self.length:
            raise EncodeError(
                self.length, len(value),
                f"Array length mismatch: expected {self.length}, got {len(value)}"
            )
            
        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)
        
        current_offset = offset
        for item in value:
            written = self.element_codec.encode_into(item, buffer, current_offset)
            current_offset += written
            
        return current_offset - offset
        
    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], 
                   offset: int = 0) -> Tuple[List, int]:
        result = []
        current_offset = offset
        bytes_read = 0
        
        try:
            for _ in range(self.length):
                item, size = self.element_codec.decode_from(buffer, current_offset)
                result.append(item)
                current_offset += size
                bytes_read += size
        except DecodeError as e:
            raise DecodeError(
                0, 0,
                f"Failed to decode array element {len(result)}: {str(e)}"
            )
            
        return result, bytes_read