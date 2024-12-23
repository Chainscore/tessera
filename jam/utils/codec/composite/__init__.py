"""
Composite type codecs for JAM protocol.

This module provides codecs for composite types including:
- Arrays (fixed length)
- Options (nullable values)
- Tuples (fixed length heterogeneous)
- Vectors (dynamic length)
- Protocols (structured data)
"""

from .arrays import Array, make_array_codec
from .options import Option, make_option_codec
from .tuples import Tuple, make_tuple_codec
from .vectors import Vector, make_vector_codec
from .protocols import Protocol, codec_protocol

__all__ = [
    # Array types
    'Array', 'make_array_codec',
    # Option types
    'Option', 'make_option_codec',
    # Tuple types
    'Tuple', 'make_tuple_codec',
    # Vector types
    'Vector', 'make_vector_codec',
    # Protocol helpers
    'Protocol', 'codec_protocol',
]