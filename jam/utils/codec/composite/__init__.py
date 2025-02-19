"""
Composite type codecs for JAM protocol.

This module provides codecs for composite types including:
- Arrays (fixed length)
- Options (nullable values)
- Vectors (dynamic length)
- Dictionaries (key-value pairs)
- Bit sequences (sequences of bits)
- Dataclasses (structured data)
"""

from .arrays import ArrayCodec
from .choices import ChoiceCodec
from .vectors import VectorCodec
from .dictionaries import DictionaryCodec
from .bit_sequences import BitSequenceCodec

__all__ = [
    "ArrayCodec",
    "ChoiceCodec",
    "VectorCodec",
    "DictionaryCodec",
    "BitSequenceCodec",
]
