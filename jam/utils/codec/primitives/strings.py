"""
String codec implementation for JAM protocol.

Implements encoding and decoding of string values according to the JAM specification.
Strings are encoded with a length prefix followed by UTF-8 encoded bytes.

Format:
    [Length: u64][UTF-8 encoded bytes]

The length is encoded using little-endian u64 format to match specification and
ensure compatibility with the maximum possible string size.
"""

from typing import Union, Tuple, Optional
import struct
from ..base import (
    Codec, EncodeError, DecodeError, 
)
from ..utils import check_buffer_size, ensure_size

class StringCodec(Codec[str]):
    """
    Codec for string values.
    
    Handles both str and static str references with UTF-8 encoding.
    Maximum string length is determined by u64 max value.
    """
    
    # Constants
    LENGTH_SIZE = 8  # Size of u64 length prefix in bytes
    LENGTH_FORMAT = '<Q'  # struct format for little-endian u64
    _length_struct = struct.Struct(LENGTH_FORMAT)
    
    def encode_size(self, value: Union[str, bytes]) -> int:
        """
        Calculate the number of bytes needed to encode the string.
        
        The size includes:
        - 8 bytes for length prefix (u64)
        - bytes needed for UTF-8 encoded string content
        
        Args:
            value: String to encode
            
        Returns:
            Total number of bytes needed
            
        Raises:
            EncodeError: If string is too large to encode
        """
        try:
            if isinstance(value, str):
                encoded = bytes(value, 'utf-8')
            elif isinstance(value, bytes):
                encoded = value
            else:
                raise EncodeError(0, 0, f"Expected str or bytes, got {type(value)}")
            
            if len(encoded) > (2**64 - 1):
                raise EncodeError(
                    0, 0,
                    "String too large to encode (exceeds u64::MAX bytes when UTF-8 encoded)"
                )
            return self.LENGTH_SIZE + len(encoded)
        except UnicodeEncodeError as e:
            raise EncodeError(0, 0, f"Failed to UTF-8 encode string: {e}")

    def encode_into(self, value: str, buffer: bytearray, offset: int = 0) -> int:
        """
        Encode a string into the provided buffer.
        
        Args:
            value: String to encode
            buffer: Target buffer
            offset: Starting position in buffer
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If buffer is too small or string cannot be encoded
        """
        if not isinstance(value, str):
            raise EncodeError(
                0, 0,
                f"Expected str, got {type(value)}"
            )
        
        try:
            # Encode string content as UTF-8
            encoded = bytes(value, 'utf-8')
            encoded_len = len(encoded)
            
            if encoded_len > (2**64 - 1):
                raise EncodeError(
                    0, 0,
                    "String too large to encode (exceeds u64::MAX bytes when UTF-8 encoded)"
                )
                
            total_size = self.LENGTH_SIZE + encoded_len
            check_buffer_size(buffer, total_size, offset)
            
            # Write length prefix
            self._length_struct.pack_into(buffer, offset, encoded_len)
            
            # Write string content
            buffer[offset + self.LENGTH_SIZE:offset + total_size] = encoded
            
            return total_size
            
        except UnicodeEncodeError as e:
            raise EncodeError(0, 0, f"Failed to UTF-8 encode string: {e}")

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], 
                   offset: int = 0) -> Tuple[str, int]:
        """
        Decode a string from the provided buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting position in buffer
            
        Returns:
            Tuple of (decoded string, bytes read)
            
        Raises:
            DecodeError: If buffer is too small or contains invalid UTF-8
        """
        # Ensure we have enough bytes for length
        ensure_size(buffer, StringCodec.LENGTH_SIZE, offset)
        
        # Read length prefix
        length = StringCodec._length_struct.unpack_from(buffer, offset)[0]
        
        # Ensure we have enough bytes for content
        total_size = StringCodec.LENGTH_SIZE + length
        ensure_size(buffer, total_size, offset)
        
        try:
            # Extract and decode content
            content = buffer[offset + StringCodec.LENGTH_SIZE:offset + total_size]
            string = bytes(content).decode('utf-8')
            return string, total_size
            
        except UnicodeDecodeError as e:
            raise DecodeError(0, 0, f"Invalid UTF-8 sequence in buffer: {e}")
        
# Codec instance
string_codec = StringCodec()