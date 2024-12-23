"""
Vector codec implementation for JAM protocol.

Implements encoding and decoding of dynamic-length sequences according to the JAM specification.
Vectors are encoded with a length prefix followed by concatenated encoded elements.

Format:
    [Length_Tag: u8][Length_Data: varies][Elements...]

Length encoding scheme:
    0x00-0xFC: Direct value (1 byte)
    0xFF: u16 value (3 bytes)
    0xFE: u24 value (4 bytes)
    0xFD: u32 value (5 bytes)
"""

from typing import TypeVar, Generic, List, Sequence, Union, Type, Optional
from ..base import (
    Codec, CodecRegistry, EncodeError, DecodeError,
    check_buffer_size, ensure_size
)


T = TypeVar('T')

class VectorCodec(Codec[Sequence[T]], Generic[T]):
    """
    Codec for dynamic-length sequences (vectors).
    
    Vectors are encoded with a variable-length prefix indicating size,
    followed by the concatenated encoded elements.
    """
    
    # Constants for length encoding
    MAX_DIRECT_LENGTH = 0xFC  # Maximum length for 1-byte encoding
    TAG_U16 = 0xFF           # Tag for 2-byte length
    TAG_U24 = 0xFE           # Tag for 3-byte length
    TAG_U32 = 0xFD           # Tag for 4-byte length
    
    def __init__(self, element_type: Type[T], element_codec: Optional[Codec[T]] = None):
        """
        Initialize vector codec.
        
        Args:
            element_type: Type of vector elements
            element_codec: Optional specific codec for elements. If None, will be
                         looked up from registry
                         
        Raises:
            ValueError: If no codec found for element_type
        """
        self.element_type = element_type
        
        # Get codec for elements
        self.element_codec = element_codec or CodecRegistry.get(element_type)
        if self.element_codec is None:
            raise ValueError(
                f"No codec registered for element type {element_type.__name__}"
            )
            
    def _encode_length(self, length: int) -> bytes:
        """
        Encode a length value according to the variable-length scheme.
        
        Args:
            length: Length to encode
            
        Returns:
            Encoded length bytes
            
        Raises:
            ValueError: If length is negative or too large
        """
        if length < 0:
            raise ValueError("Length cannot be negative")
            
        if length <= self.MAX_DIRECT_LENGTH:
            return bytes([length])
            
        if length <= 0xFFFF:  # u16 max
            return bytes([self.TAG_U16]) + length.to_bytes(2, 'little')
            
        if length <= 0xFFFFFF:  # u24 max
            return bytes([self.TAG_U24]) + length.to_bytes(3, 'little')
            
        if length <= 0xFFFFFFFF:  # u32 max
            return bytes([self.TAG_U32]) + length.to_bytes(4, 'little')
            
        raise ValueError(f"Length {length} too large to encode")

    def _decode_length(self, buffer: Union[bytes, bytearray, memoryview], 
                     offset: int = 0) -> tuple[int, int]:
        """
        Decode a length value from the buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting position in buffer
            
        Returns:
            Tuple of (decoded length, bytes read)
            
        Raises:
            DecodeError: If buffer is too small or invalid encoding
        """
        ensure_size(buffer, 1, offset)
        tag = buffer[offset]
        
        if tag <= self.MAX_DIRECT_LENGTH:
            return tag, 1
            
        if tag == self.TAG_U16:
            ensure_size(buffer, 3, offset)
            return int.from_bytes(buffer[offset+1:offset+3], 'little'), 3
            
        if tag == self.TAG_U24:
            ensure_size(buffer, 4, offset)
            return int.from_bytes(buffer[offset+1:offset+4], 'little'), 4
            
        if tag == self.TAG_U32:
            ensure_size(buffer, 5, offset)
            return int.from_bytes(buffer[offset+1:offset+5], 'little'), 5
            
        raise DecodeError(0, 0, f"Invalid length tag: {tag}")

    def encode_size(self, value: Sequence[T]) -> int:
        """
        Calculate number of bytes needed to encode vector.
        
        Args:
            value: Sequence to encode
            
        Returns:
            Number of bytes needed
            
        Raises:
            EncodeError: If sequence is invalid type or too long
        """
        if not isinstance(value, (list, tuple)):
            raise EncodeError(
                0, 0,
                f"Expected list or tuple, got {type(value)}"
            )
            
        try:
            length_size = len(self._encode_length(len(value)))
        except ValueError as e:
            raise EncodeError(0, 0, str(e))
        
        return length_size + sum(
            self.element_codec.encode_size(item) for item in value # type: ignore
        )

    def encode_into(self, value: Sequence[T], buffer: bytearray, offset: int = 0) -> int:
        """
        Encode vector into buffer.
        
        Args:
            value: Sequence to encode
            buffer: Target buffer
            offset: Starting position in buffer
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If sequence invalid or buffer too small
        """
        if not isinstance(value, (list, tuple)):
            raise EncodeError(
                0, 0,
                f"Expected list or tuple, got {type(value)}"
            )
            
        # Calculate total size and check buffer
        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)
        
        try:
            # Encode length prefix
            length_bytes = self._encode_length(len(value))
            buffer[offset:offset+len(length_bytes)] = length_bytes
            current_offset = offset + len(length_bytes)
            
            # Encode elements
            for item in value:
                if not isinstance(item, self.element_type):
                    raise EncodeError(
                        0, 0,
                        f"Expected {self.element_type.__name__}, got {type(item)}"
                    )
                written = self.element_codec.encode_into(item, buffer, current_offset) # type: ignore
                current_offset += written
                
            return current_offset - offset
            
        except ValueError as e:
            raise EncodeError(0, 0, str(e))

    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], 
                   offset: int = 0) -> tuple[List[T], int]:
        """
        Decode vector from buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting position in buffer
            
        Returns:
            Tuple of (decoded list, bytes read)
            
        Raises:
            DecodeError: If buffer too small or invalid encoding
        """
        try:
            # Decode length prefix
            length, length_size = self._decode_length(buffer, offset)
            current_offset = offset + length_size
            
            # Decode elements
            result = []
            for i in range(length):
                try:
                    item, size = self.element_codec.decode_from(buffer, current_offset) # type: ignore
                    result.append(item)
                    current_offset += size
                except DecodeError as e:
                    raise DecodeError(
                        0, 0,
                        f"Failed to decode vector element {i}: {str(e)}"
                    )
                    
            return result, current_offset - offset
            
        except DecodeError as e:
            raise DecodeError(0, 0, f"Failed to decode vector: {str(e)}")


# Type alias helper for vectors
class Vector(Generic[T], list):
    """Type alias helper for vectors."""
        
    def __class_getitem__(cls, element_type: Type[T]) -> VectorCodec[T]:
        """
        Create vector codec through type syntax.
        
        Example:
            codec = Vector[int]  # Creates codec for List[int]
        """
        return VectorCodec(element_type)

def make_vector_codec(element_type: Type[T]) -> VectorCodec[T]:
    """
    Create vector codec for given element type.
    
    Args:
        element_type: Type of vector elements
        
    Returns:
        VectorCodec instance
        
    Example:
        codec = make_vector_codec(int)
    """
    return VectorCodec(element_type)


# Register common vector types with registry
def register_vector_type(vector_type: Type) -> None:
    """
    Register codec for a specific vector type.
    
    Args:
        vector_type: Vector type to register (e.g., List[int])
        
    Example:
        register_vector_type(List[int])
    """
    from typing import get_args, get_origin
    
    if get_origin(vector_type) in (list, Sequence):
        element_type = get_args(vector_type)[0]
        CodecRegistry.register(vector_type, make_vector_codec(element_type))