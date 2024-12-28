"""
Codec implementation for JAM.

This module provides codec implementations encoding and decoding of various data types.
It includes both primitive and composite types, with support for custom codec
registration and automatic type inference.
"""

# Re-export main types and base functionality
from .base import (
    Codec, 
    EncodeError, DecodeError, 
)

# # Re-export primitive codecs
from .primitives.integers import (
    GeneralCodec,
    IntegerCodec
)
from .primitives.bools import BooleanCodec, boolean_codec
from .primitives.strings import StringCodec, string_codec
from .composite.bitsequence import BitSequenceCodec

# Re-export composite type constructors
from .composite.arrays import ArrayCodec
from .composite.options import OptionCodec
from .composite.vectors import VectorCodec
from .composite.dictionaries import DictionaryCodec
from .composite.choices import ChoiceCodec