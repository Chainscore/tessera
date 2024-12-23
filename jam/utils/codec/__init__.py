"""
JAM Protocol Codec Implementation

This module provides codec implementations for JAM protocol data types.
It includes both primitive and composite types, with support for custom codec
registration and automatic type inference.

Example Usage:
    from jam.core.codec import Codec, Array, Option, Vector, Tuple
    
    # Simple types
    encoded = encode(42)  # Uses registered int codec
    encoded = encode("hello")  # Uses registered str codec
    
    # Fixed arrays
    numbers = Array[int, 5].encode([1, 2, 3, 4, 5])
    strings = Array[str, 2].encode(["hello", "world"])
    
    # Optional values
    maybe_int = Option[int].encode(42)
    maybe_none = Option[int].encode(None)
    
    # Dynamic vectors
    numbers = Vector[int].encode([1, 2, 3])
    strings = Vector[str].encode(["hello", "world"])
    
    # Tuples
    point = Tuple[int, int].encode((10, 20))
    record = Tuple[str, int, bool].encode(("hello", 42, True))
    
    # Complex nested types
    Matrix = Array[Array[int, 3], 2]  # 2x3 matrix
    NamedPoints = Vector[Tuple[str, int, int]]  # List of named points
    OptionalMatrix = Option[Matrix]  # Maybe a matrix
"""

# Re-export main types and base functionality
from .base import (
    Codec, CodecRegistry, 
    EncodeError, DecodeError, 
)

# Re-export primitive codecs
from .primitives.integers import (
    u8, u16, u32, u64, u128, u256,
    general as general_int
)
from .primitives.bools import codec as bool_codec
from .primitives.strings import codec as str_codec

# Re-export composite type constructors
from .composite.arrays import Array, make_array_codec
from .composite.options import Option, make_option_codec
from .composite.vectors import Vector, VectorCodec
from .composite.tuples import Tuple, make_tuple_codec

# Convenience functions for encoding/decoding
def encode(value):
    """
    Encode a value using the appropriate registered codec.
    
    Args:
        value: Value to encode
        
    Returns:
        Encoded bytes
        
    Raises:
        EncodeError: If no codec is registered for the value's type
    """
    return CodecRegistry.encode(value)

def decode(type_, buffer):
    """
    Decode a value using the appropriate registered codec.
    
    Args:
        type_: Type to decode as
        buffer: Bytes to decode from
        
    Returns:
        Tuple of (decoded value, bytes read)
        
    Raises:
        DecodeError: If no codec is registered for the type
    """
    return CodecRegistry.decode(type_, buffer)

# Register default codecs
def register_default_codecs():
    """Register all default codecs with the registry."""
    from typing import Optional, List, Tuple as PyTuple
    
    # Register primitive types
    CodecRegistry.register(bool, bool_codec)
    CodecRegistry.register(str, str_codec)
    CodecRegistry.register(int, general_int)
    
    # Register specific int types if needed
    # This could be done based on value ranges
    
    # Register common container types
    def register_for_type(base_type, type_args):
        """Helper to register common container type variants."""
        for element_type in [int, str, bool]:
            CodecRegistry.register(Vector[element_type], VectorCodec(element_type))
            if base_type is PyTuple:
                for length in range(5):  # Register up to 4-tuples
                    args = (element_type,) * length
                    register_tuple_type(PyTuple[args])
            elif base_type is Optional:
                register_option_type(Optional[element_type])

    from .composite.options import register_option_type
    from .composite.tuples import register_tuple_type
    
    register_for_type(List, List)
    register_for_type(PyTuple, PyTuple)
    register_for_type(Optional, Optional)

# Initialize default codecs
register_default_codecs()