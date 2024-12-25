"""
Composite type codecs for JAM protocol.

This module provides codecs for composite types including:
- Arrays (fixed length)
- Options (nullable values)
- Tuples (fixed length heterogeneous)
- Vectors (dynamic length)
- Protocols (structured data)
"""

from .arrays import ArrayCodec
from .options import OptionCodec
from .vectors import VectorCodec
from .dictionaries import DictionaryCodec

__all__ = [
    'ArrayCodec',
    'OptionCodec',
    'VectorCodec', 
    'DictionaryCodec',
]
