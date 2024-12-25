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

from typing import TypeVar, Union, Tuple, Type, cast
from ..base import (
    Codec, EncodeError, DecodeError,
)
from ..utils import check_buffer_size, ensure_size

import math
from decimal import Decimal

# Type variable for integers
T = TypeVar('T', bound=int)

def encode(value: int, byte_size: int) -> bytes:
    return value.to_bytes(byte_size, 'little', signed=False)

def decode(buffer: Union[bytes, bytearray, memoryview]) -> int:
    return int.from_bytes(buffer, 'little', signed=False)

class IntegerCodec(Codec[T]):
    """
    Base codec for fixed-width integers.
    
    Encodes integers in little-endian format with fixed width.
    Supports both signed and unsigned values.
    """
    
    def __init__(self, byte_size: int, python_type: Type[int]):
        """
        Initialize codec for specific integer type.
        
        Args:
            byte_size: Number of bytes for encoded value
            python_type: Python type for values
        """
        self.byte_size = byte_size
        self.python_type = python_type

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
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If value out of bounds or buffer too small
        """
        if not 0 <= value < (2**(8*self.byte_size)):
            raise EncodeError(
                expected=0, 
                actual=value,
                message="Integer value out of bounds"
            )
            
        check_buffer_size(buffer, self.byte_size, offset)
        buffer[offset:offset+self.byte_size] = encode(value, self.byte_size)
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
        value = int.from_bytes(buffer[offset:offset+self.byte_size], 'little')
        return cast(T, self.python_type(value)), self.byte_size

class GeneralCodec(Codec[int]):
    """
    Codec for variable-length integer encoding.
    
    Implements variable length int encoding scheme
    """

    @staticmethod
    def l(x):
        return math.floor(Decimal(x).ln()/(Decimal(7)*Decimal(2).ln()))
    
    def encode_size(self, value: int) -> int:
        """Calculate encoded size based on value magnitude."""
        if not isinstance(value, int):
            raise EncodeError(
                expected=int,
                actual=type(value),
                message="Value must be an integer"
            )
        
        if value < 0:
            raise EncodeError(
                expected=0,
                actual=value,
                message="Cannot encode negative values"
            )
        
        if value < 2**7:
            return 1
        elif value < 2**(7*9):
            return 1 + self.l(value)
        elif value < 2**64:
            return 9
        else:
            raise EncodeError(
                expected=0,
                actual=value,
                message="Value too large for encoding"
            )

    def encode_into(self, value: int, buffer: bytearray, offset: int = 0) -> int:
        """
        Encode integer using variable-length scheme.
        
        Args:
            value: Integer to encode
            buffer: Target buffer
            offset: Starting offset
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If value invalid or buffer too small
        """
        if not isinstance(value, int):
            raise EncodeError(
                expected=int,
                actual=type(value),
                message="Value must be an integer"
            )
        
        if value < 0:
            raise EncodeError(
                expected=0,
                actual=value,
                message="Cannot encode negative values"
            )
        
        if value < 2**7:
            buffer[offset] = value
            return 1

        size = self.encode_size(value)
        check_buffer_size(buffer, size, offset)
        if(value < 2**(7*8)):
            _l = self.l(value)
            buffer[offset: offset + 1] = IntegerCodec(1, int).encode(2**8 - 2**(8-_l) + math.floor(Decimal(value)/(Decimal(2)**(_l*8))))
            buffer[offset + 1: offset + _l] = IntegerCodec(_l, int).encode(value % 2**(_l*8))
        elif value < 2**64:
            buffer[offset: offset + 1] = IntegerCodec(1, int).encode(2**8 - 1)
            buffer[offset + 1: offset + 8] = IntegerCodec(8, int).encode(value)
        else:
            raise EncodeError(
                expected=0,
                actual=value,
                message="Value too large for encoding"
            )
        
        return size

    def decode_from(self, buffer: Union[bytes, bytearray, memoryview],
                   offset: int = 0) -> Tuple[int, int]:
        """
        Decode integer using variable-length scheme.
        
        Args:
            buffer: Source buffer
            offset: Starting offset
            
        Returns:
            Tuple of (decoded value, bytes read)
            
        Raises:
            DecodeError: If buffer too small or invalid encoding
        """
        ensure_size(buffer, 1, offset)
        tag = buffer[offset]

        if tag < 2**7:
            return tag, 1
            
        if tag == 2**8 - 1:
            # Full 64-bit encoding
            ensure_size(buffer, 9, offset)
            value, _ = IntegerCodec(8, int).decode_from(buffer[offset+1:offset+9])
            return value, 9
        else:
            # Variable length encoding
            l = math.floor(Decimal(8)-(Decimal(2**8) - Decimal(tag)).ln()/Decimal(2).ln())
            ensure_size(buffer, l+1, offset)
            alpha = tag + 2**(8-l) - 2**8
            beta, _ = IntegerCodec(l, int).decode_from(buffer[offset+1:offset+l+1])
            return alpha*2**(l*8) + beta, l+1

# Specialized types for each integer width
class U8(int): 
    byte_size = 1
class U16(int): 
    byte_size = 2
class U32(int): 
    byte_size = 4
class U64(int): 
    byte_size = 8
class U128(int): 
    byte_size = 16
class U256(int): 
    byte_size = 32
# Codec instances with proper types
u8_codec = IntegerCodec(U8.byte_size, U8)
u16_codec = IntegerCodec(U16.byte_size, U16)
u32_codec = IntegerCodec(U32.byte_size, U32)
u64_codec = IntegerCodec(U64.byte_size, U64)
u128_codec = IntegerCodec(U128.byte_size, U128)
u256_codec = IntegerCodec(U256.byte_size, U256)

# General variable length codec
general_codec = GeneralCodec()