"""
Boolean codec implementation for JAM protocol.

Implements encoding and decoding of boolean values according to the JAM specification.
Booleans are encoded as a single byte with 0 for False and 1 for True.
"""

from typing import Tuple, Union
from ..base import Codec, EncodeError, DecodeError
from ..utils import check_buffer_size, ensure_size

class BooleanCodec(Codec[bool]):
    """
    Codec for boolean values.
    
    Encoding scheme:
    - False -> b''
    - True  -> b'00'
    
    Any non-zero value is decoded as True for robustness.
    """
    
    def encode_size(self, value: bool) -> int:
        """
        Calculate size needed to encode a boolean value.
        
        Args:
            value: Boolean to encode
            
        Returns:
            Always returns 1 as booleans are encoded as a single byte
        """
        return 1
        
    def encode_into(self, value: bool, buffer: bytearray, offset: int = 0) -> int:
        """
        Encode a boolean value into the provided buffer.
        
        Args:
            value: Boolean to encode
            buffer: Target buffer
            offset: Starting position in buffer
            
        Returns:
            Number of bytes written (always 1)
            
        Raises:
            EncodeError: If the buffer is too small or value is invalid type
        """
        check_buffer_size(buffer, 1, offset)
        buffer[offset] = 1 if value else 0
        return 1
        
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], 
                   offset: int = 0) -> Tuple[bool, int]:
        """
        Decode a boolean value from the provided buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting position in buffer
            
        Returns:
            Tuple of (decoded boolean, bytes read)
            
        Raises:
            DecodeError: If the buffer is too small
        """
        ensure_size(buffer, 1, offset)
        # Any non-zero value is considered True
        value = bool(buffer[offset])
        return value, 1
    
# Codec instance
boolean_codec = BooleanCodec()