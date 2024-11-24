"""
Integer codec implementations for JAM protocol encoding specification.

Implements both fixed-width integers and the general variable-length integer 
encoding scheme specified in JAM graypaper Appendix C.

Fixed width integers are encoded in little-endian format.
Variable length integers use the following scheme:
- 0x00-0xFC: Direct value (1 byte)
- 0xFD: u16 value (3 bytes) 
- 0xFE: u24 value (4 bytes)
- 0xFF: u32 value (5 bytes)
"""

from typing import TypeVar, Dict, Union, Tuple, Type, Optional, Final, cast
import struct
from ..base import (
    Codec, CodecRegistry, EncodeError, DecodeError,
    check_buffer_size, ensure_size
)

# Type variable for integers
T = TypeVar('T', bound=int)

# Constants for variable length encoding
DIRECT_ENCODING_MAX: Final[int] = 0xFC
TAG_U16: Final[int] = 0xFD
TAG_U24: Final[int] = 0xFE  
TAG_U32: Final[int] = 0xFF

# Maximum values for each type
MAX_U8: Final[int] = 0xFF
MAX_U16: Final[int] = 0xFFFF
MAX_U24: Final[int] = 0xFFFFFF
MAX_U32: Final[int] = 0xFFFFFFFF
MAX_U64: Final[int] = 0xFFFFFFFFFFFFFFFF

class IntegerCodec(Codec[T]):
    """
    Base codec for fixed-width integers.
    
    Encodes integers in little-endian format with fixed width.
    Supports both signed and unsigned values.
    """
    
    def __init__(self, byte_size: int, signed: bool, python_type: Type[int],
                 min_value: int, max_value: int):
        """
        Initialize codec for specific integer type.
        
        Args:
            byte_size: Number of bytes for encoded value
            signed: Whether type is signed
            python_type: Python type for values
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        """
        self.byte_size = byte_size
        self.signed = signed
        self.python_type = python_type
        self.min_value = min_value
        self.max_value = max_value
        
        # Create struct format for efficient encoding/decoding
        self._format = '<' + {
            1: 'b' if signed else 'B',
            2: 'h' if signed else 'H', 
            4: 'i' if signed else 'I',
            8: 'q' if signed else 'Q'
        }[byte_size]
        self._struct = struct.Struct(self._format)

    def encode_size(self, value: T) -> int:
        """Get encoded size (fixed for given type)."""
        return self.byte_size

    def encode_into(self, value: T, buffer: bytearray, 
                   offset: int = 0) -> int:
        """
        Encode integer into buffer.
        
        Args:
            value: Integer to encode
            buffer: Target buffer
            offset: Starting offset
            context: Optional encoding context
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If value out of bounds or buffer too small
        """
        if not isinstance(value, int):
            raise EncodeError(
                expected="int",
                actual=type(value).__name__
            )
            
        if not self.min_value <= value <= self.max_value:
            raise EncodeError(
                expected=0,
                actual=value,
                message="Integer value out of bounds"
            )
            
        check_buffer_size(buffer, self.byte_size, offset)
        self._struct.pack_into(buffer, offset, value)
        return self.byte_size

    def decode_from(self, buffer: Union[bytes, bytearray, memoryview],
                   offset: int = 0) -> Tuple[T, int]:
        """
        Decode integer from buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting offset
            context: Optional decoding context
            
        Returns:
            Tuple of (decoded value, bytes read)
            
        Raises:
            DecodeError: If buffer too small
        """
        ensure_size(buffer, self.byte_size, offset)
        value = self._struct.unpack_from(buffer, offset)[0]
        return cast(T, self.python_type(value)), self.byte_size

class GeneralCodec(Codec[int]):
    """
    Codec for variable-length integer encoding.
    
    Implements JAM protocol variable length encoding scheme:
    - 0x00-0xFC: Direct value (1 byte)
    - 0xFD: u16 value (3 bytes)
    - 0xFE: u24 value (4 bytes) 
    - 0xFF: u32 value (5 bytes)
    """
    
    def encode_size(self, value: int) -> int:
        """Calculate encoded size based on value magnitude."""
        if not isinstance(value, int):
            raise EncodeError(
                expected=0,
                actual=value,
                message="Expected integer"
            )
            
        if value < 0:
            raise EncodeError(
                expected=0,
                actual=value,
                message="Cannot encode negative values"
            )
            
        if value <= DIRECT_ENCODING_MAX:
            return 1
        elif value <= MAX_U16:
            return 3  # tag + 2 bytes
        elif value <= MAX_U24:
            return 4  # tag + 3 bytes
        elif value <= MAX_U32:
            return 5  # tag + 4 bytes
        else:
            raise EncodeError(
                expected=0,
                actual=value,
                message="Value too large for encoding"
            )

    def encode_into(self, value: int, buffer: bytearray,
                   offset: int = 0) -> int:
        """
        Encode integer using variable-length scheme.
        
        Args:
            value: Integer to encode
            buffer: Target buffer
            offset: Starting offset
            context: Optional encoding context
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If value invalid or buffer too small
        """
        size = self.encode_size(value)
        check_buffer_size(buffer, size, offset)
        
        if value <= DIRECT_ENCODING_MAX:
            buffer[offset] = value
            return 1
            
        if value <= MAX_U16:
            buffer[offset] = TAG_U16
            buffer[offset+1:offset+3] = value.to_bytes(2, 'little')
            return 3
            
        if value <= MAX_U24:
            buffer[offset] = TAG_U24
            buffer[offset+1:offset+4] = value.to_bytes(3, 'little')
            return 4
            
        if value <= MAX_U32:
            buffer[offset] = TAG_U32
            buffer[offset+1:offset+5] = value.to_bytes(4, 'little')
            return 5
            
        raise EncodeError(
            expected=0,
            actual=value,
            message="Value too large for encoding"
        )

    def decode_from(self, buffer: Union[bytes, bytearray, memoryview],
                   offset: int = 0) -> Tuple[int, int]:
        """
        Decode integer using variable-length scheme.
        
        Args:
            buffer: Source buffer
            offset: Starting offset
            context: Optional decoding context
            
        Returns:
            Tuple of (decoded value, bytes read)
            
        Raises:
            DecodeError: If buffer too small or invalid encoding
        """
        ensure_size(buffer, 1, offset)
        tag = buffer[offset]
        
        if tag <= DIRECT_ENCODING_MAX:
            return tag, 1
            
        if tag == TAG_U16:
            ensure_size(buffer, 3, offset)
            value = int.from_bytes(buffer[offset+1:offset+3], 'little')
            if value <= DIRECT_ENCODING_MAX:
                raise DecodeError(
                    expected=0,
                    actual=value,
                    message="Invalid encoding: value too small for u16 tag"
                )
            return value, 3
            
        if tag == TAG_U24:
            ensure_size(buffer, 4, offset)
            value = int.from_bytes(buffer[offset+1:offset+4], 'little')
            if value <= MAX_U16:
                raise DecodeError(
                    expected=0,
                    actual=value,
                    message="Invalid encoding: value too small for u24 tag"
                )
            return value, 4
            
        if tag == TAG_U32:
            ensure_size(buffer, 5, offset)
            value = int.from_bytes(buffer[offset+1:offset+5], 'little')
            if value <= MAX_U24:
                raise DecodeError(
                    expected=0,
                    actual=value,
                    message="Invalid encoding: value too small for u32 tag"
                )
            return value, 5
            
        raise DecodeError(
            expected=0,  # Expected value doesn't apply here, using 0 as default
            actual=tag,  # Pass the invalid tag as the actual value
            message="Invalid tag in variable length encoding"
        )

# Then create specialized types for each integer width
class U8(int): pass
class U16(int): pass
class U32(int): pass
class U64(int): pass
class I8(int): pass
class I16(int): pass
class I32(int): pass
class I64(int): pass

# Create codec instances with proper types
u8 = IntegerCodec(1, False, U8, 0, MAX_U8)
u16 = IntegerCodec(2, False, U16, 0, MAX_U16)
u32 = IntegerCodec(4, False, U32, 0, MAX_U32)
u64 = IntegerCodec(8, False, U64, 0, MAX_U64)

i8 = IntegerCodec(1, True, I8, -128, 127)
i16 = IntegerCodec(2, True, I16, -32768, 32767)
i32 = IntegerCodec(4, True, I32, -0x80000000, 0x7FFFFFFF)
i64 = IntegerCodec(8, True, I64, -0x8000000000000000, 0x7FFFFFFFFFFFFFFF)


# General variable length codec
general = GeneralCodec()

# Register specialized types
CodecRegistry.register(U8, u8)
CodecRegistry.register(U16, u16)
CodecRegistry.register(U32, u32)
CodecRegistry.register(U64, u64)
CodecRegistry.register(I8, i8)
CodecRegistry.register(I16, i16)
CodecRegistry.register(I32, i32)
CodecRegistry.register(I64, i64)

# General int still uses GeneralCodec
CodecRegistry.register(int, general)