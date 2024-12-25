"""
Primitive type codecs for JAM protocol.

This module provides codecs for primitive types including:
- Integers (fixed width and general)
- Booleans
- Strings
"""

from .integers import (
    U8, U16, U32, U64, U128, U256,
    GeneralCodec as GeneralIntCodec,
    u8_codec, u16_codec, u32_codec, u64_codec, u128_codec, u256_codec,
    general_codec
)
from .bools import BooleanCodec as BoolCodec
from .strings import StringCodec as StrCodec
from .bitsequence import BitSequenceCodec

__all__ = [
    # Integer codecs
    'U8', 'U16', 'U32', 'U64', 'U128', 'U256',
    
    'GeneralIntCodec',
    # Boolean codec
    'BoolCodec',
    # String codec
    'StrCodec',
    'BitSequenceCodec',
]