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

from jam.utils.codec.primitives.integers import GeneralCodec
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

    @staticmethod
    def _encode(value: Union[str, bytes]) -> bytes:
        if isinstance(value, str):
            return bytes(value, 'utf-8')
        elif isinstance(value, bytes):
            return value
        else:
            raise EncodeError(0, 0, f"Expected str or bytes, got {type(value)}")
    
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
        enc_len = len(StringCodec._encode(value))
        return GeneralCodec().encode_size(enc_len) + enc_len

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
            total_size = self.encode_size(value)
            check_buffer_size(buffer, total_size, offset)
            
            # Write length prefix
            length_size = GeneralCodec().encode_into(len(value), buffer, offset)
            
            # Write string content
            buffer[offset + length_size: offset + total_size] = StringCodec._encode(value)
            
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
        # Read length prefix
        length, length_size = GeneralCodec().decode_from(buffer, offset)
        
        # Ensure we have enough bytes for content
        total_size = length_size + length
        ensure_size(buffer, total_size, offset)
        
        try:
            # Extract and decode content
            content = buffer[offset + length_size:offset + total_size]
            string = bytes(content).decode('utf-8')
            return string, total_size
            
        except UnicodeDecodeError as e:
            raise DecodeError(0, 0, f"Invalid UTF-8 sequence in buffer: {e}")
        
# Codec instance
string_codec = StringCodec()