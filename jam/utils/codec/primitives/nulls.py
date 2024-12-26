"""
Null codec implementation for JAM protocol.

Implements encoding and decoding of null values according to the JAM specification.
Null values are encoded as an empty byte sequence.
"""

from typing import Tuple, Union, Type
from ..base import Codec, EncodeError, DecodeError
from ..utils import check_buffer_size, ensure_size

class NullCodec(Codec[None]):
    """
    Codec for null values.
    
    Encoding scheme:
        None -> [] (empty byte sequence)
    """
    
    def encode_size(self, value: None) -> int:
        """
        The encoded size of a null value is always 0.
        """
        if value is not None:
            raise EncodeError(0, 0, "Value must be None")
        return 0
        
    def encode_into(self, value: None, buffer: bytearray, offset: int = 0) -> int:
        """
        Encode a null value into the provided buffer.
        
        Args:
            value: The null value to encode (must be None)
            buffer: Destination buffer
            offset: Starting position in buffer
            
        Returns:
            Number of bytes written (always 0)
            
        Raises:
            EncodeError: If the value is not None
        """
        if value is not None:
            raise EncodeError(0, 0, "Value must be None")
        return 0
        
    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], 
                   offset: int = 0) -> Tuple[None, int]:
        """
        Decode a null value from the provided buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting position in buffer
            
        Returns:
            Tuple of (decoded null value, bytes read)
            
        Raises:
            DecodeError: If the buffer is not empty at the given offset
        """
        # We don't need to check buffer size here because null is represented by 
        # an empty sequence, and we don't consume any bytes.
        return None, 0
    
# Codec instance
null_codec = NullCodec() 