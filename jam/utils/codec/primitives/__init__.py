"""
Primitive type codecs for JAM protocol.

This module provides codecs for primitive types including:
- Integers (fixed width and general)
- Booleans
- Strings
- Bit sequences
"""

from .integers import GeneralCodec, IntegerCodec
from .bools import BooleanCodec
from .strings import StringCodec

__all__ = [
    # Integer codecs
    "IntegerCodec",
    "GeneralCodec",
    # Boolean codec
    "BooleanCodec",
    # String codec
    "StringCodec",
]
