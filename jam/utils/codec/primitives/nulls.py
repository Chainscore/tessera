"""
Null codec implementation for JAM protocol.

Implements encoding and decoding of null values according to the JAM specification.
Null values are encoded as an empty byte sequence.
"""

from typing import Tuple, Union, Optional
from jam.utils.codec import Codec, EncodeError

class NullCodec(Codec[None]):
    """
    Codec for null values.
    
    Null values are encoded as empty byte sequences. This is the simplest possible
    codec as it doesn't actually write any bytes.
    
    Examples:
        >>> codec = NullCodec()
        >>> encoded = codec.encode(None)
        >>> assert encoded == b""
        >>> decoded, size = codec.decode_from(b"")
        >>> assert decoded is None
        >>> assert size == 0
    """
    
    def encode_size(self, value: Optional[None]) -> int:
        """
        Calculate encoded size for null value.
        
        Args:
            value: Must be None
            
        Returns:
            Always returns 0
            
        Raises:
            EncodeError: If value is not None
        """
        if value is not None:
            raise EncodeError(0, 0, "Value must be None")
        return 0
        
    def encode_into(self, value: Optional[None], buffer: bytearray, offset: int = 0) -> int:
        """
        Encode a null value into the provided buffer.
        
        Args:
            value: Must be None
            buffer: Destination buffer
            offset: Starting position in buffer
            
        Returns:
            Always returns 0
            
        Raises:
            EncodeError: If value is not None
        """
        if value is not None:
            raise EncodeError(0, 0, "Value must be None")
        return 0
        
    @staticmethod
    def decode_from(
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> Tuple[None, int]:
        """
        Decode a null value from the provided buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting position in buffer
            
        Returns:
            Tuple of (None, 0)
        """
        return None, 0