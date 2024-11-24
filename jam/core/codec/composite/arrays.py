"""
Array codec implementation for JAM protocol.

Implements encoding and decoding of fixed-length arrays according to the JAM specification.
Arrays are encoded by concatenating their encoded elements with no length prefix.
The length is known at compile-time in Rust; in Python we enforce it at runtime.

Maximum array size is 1000 elements as per specification.
"""

from typing import TypeVar, Generic, List, Tuple, Union, Sequence, Optional, Type
from ..base import (
    Codec, CodecRegistry, EncodeError, DecodeError,
    check_buffer_size, ensure_size
)

T = TypeVar('T')

class ArrayCodec(Codec[Sequence[T]], Generic[T]):
    """
    Codec for fixed-length arrays/sequences.
    
    Arrays are encoded by concatenating their encoded elements in order.
    The length is fixed and known at encoding/decoding time.
    """
    
    # Maximum array size constant from specification
    MAX_SIZE = 1000
    
    def __init__(self, element_type: Type[T], length: int, element_codec: Optional[Codec[T]] = None):
        """
        Initialize array codec.
        
        Args:
            element_type: Type of array elements
            length: Fixed length of arrays to encode/decode
            element_codec: Optional specific codec for elements. If None, will be 
                         looked up from registry
                         
        Raises:
            ValueError: If length exceeds maximum or no codec found for element_type
        """
        if length > self.MAX_SIZE:
            raise ValueError(
                f"Array length {length} exceeds maximum allowed size {self.MAX_SIZE}"
            )
        if length < 0:
            raise ValueError(f"Array length cannot be negative: {length}")
            
        self.length = length
        self.element_type = element_type
        
        # Get codec for elements
        self.element_codec = element_codec or CodecRegistry.get(element_type)
        if self.element_codec is None:
            raise ValueError(
                f"No codec registered for element type {element_type.__name__}"
            )
            
    def encode_size(self, value: Sequence[T]) -> int:
        """
        Calculate number of bytes needed to encode array.
        
        Args:
            value: Sequence to encode
            
        Returns:
            Number of bytes needed
            
        Raises:
            EncodeError: If sequence length doesn't match expected length
        """
        if len(value) != self.length:
            raise EncodeError(
                self.length, len(value),
                f"Array length mismatch: expected {self.length}, got {len(value)}"
            )
            
        if self.element_codec is None:
            raise EncodeError(0, 0, "Element codec is None")
            
        return sum(self.element_codec.encode_size(item) for item in value)
        
    def encode_into(self, value: Sequence[T], buffer: bytearray, offset: int = 0) -> int:
        """
        Encode array into buffer.
        
        Args:
            value: Sequence to encode
            buffer: Target buffer
            offset: Starting position in buffer
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If sequence length is wrong or buffer too small
        """
        if len(value) != self.length:
            raise EncodeError(
                self.length, len(value),
                f"Array length mismatch: expected {self.length}, got {len(value)}"
            )
            
        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)
        
        current_offset = offset
        for item in value:
            if self.element_codec is None:
                raise EncodeError(0, 0, "Element codec is None")
            written = self.element_codec.encode_into(item, buffer, current_offset)
            current_offset += written
            
        return current_offset - offset
        
    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], 
                   offset: int = 0) -> Tuple[List[T], int]:
        """
        Decode array from buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting position in buffer
            
        Returns:
            Tuple of (decoded list, bytes read)
            
        Raises:
            DecodeError: If buffer is too small or invalid encoding
        """
        result = []
        current_offset = offset
        bytes_read = 0
        
        try:
            for _ in range(self.length):
                if self.element_codec is None:
                    raise DecodeError(0, 0, "Element codec is None")
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


def make_array_codec(element_type: Type[T], length: int) -> ArrayCodec[T]:
    """
    Create array codec for given element type and length.
    
    Args:
        element_type: Type of array elements
        length: Fixed length of arrays to encode/decode
        
    Returns:
        ArrayCodec instance
        
    Raises:
        ValueError: If length exceeds maximum or no codec for element_type
    """
    return ArrayCodec(element_type, length)


# Type alias helper for fixed-length arrays
class Array(Generic[T], List[T]):
    """Type alias helper for fixed-length arrays."""

    def __init__(self, length: int):
        self.length = length
        
    def __class_getitem__(cls, key: Tuple[Type[T], int]) -> ArrayCodec[T]:
        """
        Create array codec through type syntax.
        
        Example:
            codec = Array[int, 5]  # Creates codec for 5-element int array
        """
        if not isinstance(key, tuple) or len(key) != 2:
            raise TypeError("Array type requires [element_type, length]")
            
        element_type, length = key
        if not isinstance(length, int):
            raise TypeError("Array length must be an integer")
            
        return make_array_codec(element_type, length)