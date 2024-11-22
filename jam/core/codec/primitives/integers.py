"""
Integer codec implementations for JAM protocol.

This module implements encoding and decoding for various integer types according to 
the JAM protocol specification (Appendix C). It includes both fixed-width integers
and general number encoding.
"""

from typing import TypeVar, Dict, Union, Tuple, Type
import struct
from ..base import Codec, EncodeError, DecodeError, check_buffer_size, ensure_size

T = TypeVar('T', bound=int)

class IntegerCodec(Codec[T]):
    """Base codec for fixed-width integers."""
    
    def __init__(self, byte_size: int, signed: bool, python_type: Type[int],
                 min_value: int, max_value: int):
        """
        Initialize the codec.
        
        Args:
            byte_size: Number of bytes for this integer type
            signed: Whether this is a signed integer type
            python_type: The Python type this codec handles
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        """
        self.byte_size = byte_size
        self.signed = signed
        self.python_type = python_type
        self.min_value = min_value
        self.max_value = max_value
        # Create struct format string based on endianness and size
        self._struct_format = '<' + {
            1: 'b' if signed else 'B',
            2: 'h' if signed else 'H',
            4: 'i' if signed else 'I',
            8: 'q' if signed else 'Q',
        }[byte_size]
        self._struct = struct.Struct(self._struct_format)

    def encode_size(self, value: T) -> int:
        """Calculate encoded size (fixed for given integer type)."""
        return self.byte_size

    def encode_into(self, value: T, buffer: bytearray, offset: int = 0) -> int:
        """
        Encode an integer into the buffer.
        
        Args:
            value: Integer to encode
            buffer: Target buffer
            offset: Starting offset in buffer
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If value is out of bounds or buffer too small
        """
        if not isinstance(value, int):
            raise EncodeError(
                self.byte_size, 0,
                f"Expected int, got {type(value)}"
            )
        
        if not self.min_value <= value <= self.max_value:
            raise EncodeError(
                self.byte_size, 0,
                f"Value {value} out of bounds for {self.python_type.__name__}"
            )

        check_buffer_size(buffer, self.byte_size, offset)
        self._struct.pack_into(buffer, offset, value)
        return self.byte_size

    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], 
                   offset: int = 0) -> Tuple[T, int]:
        """
        Decode an integer from the buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting offset in buffer
            
        Returns:
            Tuple of (decoded value, bytes read)
            
        Raises:
            DecodeError: If buffer is too small
        """
        ensure_size(buffer, self.byte_size, offset)
        value = self._struct.unpack_from(buffer, offset)[0]
        return self.python_type(value), self.byte_size


class GeneralCodec(Codec[int]):
    """
    Codec for general number encoding as specified in JAM protocol.
    
    This implements the variable-length encoding scheme that minimizes bytes
    for smaller numbers while supporting the full u64 range.
    """
    
    MAX_ENCODED_SIZE = 9  # Maximum possible encoded size for any number

    def encode_size(self, value: int) -> int:
        """Calculate the number of bytes needed to encode the value."""
        if value < 0:
            raise EncodeError(0, 0, "Cannot encode negative values")
            
        if value == 0:
            return 1
            
        # Determine required size based on value ranges
        if value < 128:                    return 1  # 2^7
        if value < 16384:                  return 2  # 2^14
        if value < 2097152:                return 3  # 2^21
        if value < 268435456:              return 4  # 2^28
        if value < 34359738368:            return 5  # 2^35
        if value < 4398046511104:          return 6  # 2^42
        if value < 562949953421312:        return 7  # 2^49
        if value < 72057594037927936:      return 8  # 2^56
        if value <= 18446744073709551615:  return 9  # 2^64
        
        raise EncodeError(0, 0, f"Value {value} too large for encoding")

    def encode_into(self, value: int, buffer: bytearray, offset: int = 0) -> int:
        """
        Encode a general number using variable-length encoding.
        
        Args:
            value: Number to encode
            buffer: Target buffer
            offset: Starting offset in buffer
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If value is invalid or buffer too small
        """
        if value < 0:
            raise EncodeError(0, 0, "Cannot encode negative values")

        size = self.encode_size(value)
        check_buffer_size(buffer, size, offset)

        if value == 0:
            buffer[offset] = 0
            return 1

        if value < (1 << (7 * size)):
            # Regular encoding path
            l = size - 1
            # First byte: 2^8 - 2^(8-l) + floor_div(value, 2^(8l))
            decoded_var = (1 << 8) - (1 << (8 - l)) + (value >> (8 * l))
            buffer[offset] = decoded_var & 0xFF
            
            # Remaining bytes
            remaining = value & ((1 << (8 * l)) - 1)
            for i in range(l):
                buffer[offset + l - i] = remaining & 0xFF
                remaining >>= 8
                
        else:
            # Full 64-bit encoding path
            buffer[offset] = 0xFF  # Signal full encoding
            for i in range(8):
                buffer[offset + 8 - i] = value & 0xFF
                value >>= 8

        return size

    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], 
                   offset: int = 0) -> Tuple[int, int]:
        """
        Decode a general number.
        
        Args:
            buffer: Source buffer
            offset: Starting offset in buffer
            
        Returns:
            Tuple of (decoded value, bytes read)
            
        Raises:
            DecodeError: If buffer is too small or invalid encoding
        """
        ensure_size(buffer, 1, offset)
        
        first_byte = buffer[offset]
        
        if first_byte == 0:
            return 0, 1
            
        if first_byte == 0xFF:
            # Full 64-bit encoding
            ensure_size(buffer, 9, offset)
            value = 0
            for i in range(8):
                value = (value << 8) | buffer[offset + i + 1]
            return value, 9
            
        # Calculate l (number of additional bytes) from first byte
        l = 1
        test = first_byte
        while test & 0x80:
            l += 1
            test = (test << 1) & 0xFF
            
        ensure_size(buffer, l + 1, offset)
        
        # Extract value from remaining bytes
        value = (first_byte - (0xFF - (1 << (8 - l)) + 1)) << (8 * l)
        for i in range(l):
            value |= buffer[offset + 1 + i] << (8 * (l - 1 - i))
            
        return value, l + 1


# Create codec instances for standard integer types
u8 = IntegerCodec(1, False, int, 0, 255)
u16 = IntegerCodec(2, False, int, 0, 65535)
u32 = IntegerCodec(4, False, int, 0, 4294967295)
u64 = IntegerCodec(8, False, int, 0, 18446744073709551615)

i8 = IntegerCodec(1, True, int, -128, 127)
i16 = IntegerCodec(2, True, int, -32768, 32767)
i32 = IntegerCodec(4, True, int, -2147483648, 2147483647)
i64 = IntegerCodec(8, True, int, -9223372036854775808, 9223372036854775807)

# General number codec instance
general = GeneralCodec()

# Register codecs with registry
from ..base import CodecRegistry

# Map Python integer ranges to appropriate fixed-width codecs
RANGE_CODECS = [
    ((-128, 127), i8),
    ((-32768, 32767), i16),
    ((-2147483648, 2147483647), i32),
    ((-9223372036854775808, 9223372036854775807), i64),
    ((0, 255), u8),
    ((0, 65535), u16),
    ((0, 4294967295), u32),
    ((0, 18446744073709551615), u64),
]

def get_codec_for_value(value: int) -> Codec[int]:
    """Get the most appropriate codec for a given integer value."""
    for (min_val, max_val), codec in RANGE_CODECS:
        if min_val <= value <= max_val:
            return codec
    raise ValueError(f"No suitable codec for value: {value}")

# Register int type with the general codec as default
CodecRegistry.register(int, general)