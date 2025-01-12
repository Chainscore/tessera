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
from .choices import ChoiceCodec
from .vectors import VectorCodec
from .dictionaries import DictionaryCodec
from .bit_sequences import BitSequenceCodec
from .dataclasses import decodable_dataclass

__all__ = [
    'ArrayCodec',
    'ChoiceCodec',
    'VectorCodec', 
    'DictionaryCodec',
    'BitSequenceCodec',
    'decodable_dataclass',
]
