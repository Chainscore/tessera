"""
Primitive type codecs for JAM protocol.

This module provides codecs for primitive types including:
- Integers (fixed width and general)
- Booleans
- Strings
"""

from .integers import (
    u8, u16, u32, u64, u128, u256,
    general as general_int
)
from .bools import codec as bool_codec
from .strings import codec as str_codec

__all__ = [
    # Integer codecs
    'u8', 'u16', 'u32', 'u64', 'u128', 'u256',
    'general_int',
    # Boolean codec
    'bool_codec',
    # String codec
    'str_codec',
]