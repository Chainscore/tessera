"""Base types for the JAM protocol."""
from dataclasses import dataclass
from typing import NewType

# Simple integer types
U8 = NewType('U8', int)
U16 = NewType('U16', int)
U32 = NewType('U32', int)
U64 = NewType('U64', int)

# Byte sequence types
ByteSequence = NewType('ByteSequence', bytes)
ByteArray32 = NewType('ByteArray32', bytes)

def validate_u8(value: int) -> U8:
    """Validate and create a U8 value."""
    if not 0 <= value <= 255:
        raise ValueError(f"U8 value must be between 0 and 255, got {value}")
    return U8(value)

def validate_u16(value: int) -> U16:
    """Validate and create a U16 value."""
    if not 0 <= value <= 65535:
        raise ValueError(f"U16 value must be between 0 and 65535, got {value}")
    return U16(value)

def validate_u32(value: int) -> U32:
    """Validate and create a U32 value."""
    if not 0 <= value <= 4294967295:
        raise ValueError(f"U32 value must be between 0 and 4294967295, got {value}")
    return U32(value)

def validate_u64(value: int) -> U64:
    """Validate and create a U64 value."""
    if not 0 <= value <= 18446744073709551615:
        raise ValueError(f"U64 value must be between 0 and 18446744073709551615, got {value}")
    return U64(value)

def validate_byte_array32(value: bytes) -> ByteArray32:
    """Validate and create a ByteArray32 value."""
    if len(value) != 32:
        raise ValueError(f"ByteArray32 must be exactly 32 bytes, got {len(value)}")
    return ByteArray32(value) 