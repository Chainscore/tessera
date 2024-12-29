"""
Primitive type codecs for JAM protocol.

This module provides codecs for primitive types including:
- Integers (fixed width and general)
- Booleans
- Strings
- Bit sequences
"""

from .integers import (
    GeneralCodec,
    IntegerCodec
)
from .bools import BooleanCodec as BoolCodec, boolean_codec
from .strings import StringCodec as StrCodec, string_codec

__all__ = [
    # Integer codecs
    'IntegerCodec',
    'GeneralCodec',
    # Boolean codec
    'BoolCodec',
    # String codec
    'StrCodec',
    # Codecs
    'boolean_codec',
    'string_codec',
]