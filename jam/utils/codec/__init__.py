"""
Codecs for JAM.

This module provides codec implementations encoding and decoding of various data types.
It includes both primitive and composite types, with support for custom codec
registration and automatic type inference.
"""

# Re-export main types and base functionality
from .base import (
    Codec, 
    EncodeError, DecodeError, 
    BufferError,
    Codable,
)

# Re-export JSON codec
from .json import JsonCodec, JsonSerializable, json_serializable

# Re-export primitive codecs
from .primitives import (
    GeneralCodec,
    IntegerCodec,
    BooleanCodec,
    StringCodec,
)

# Re-export composite type constructors
from .composite import BitSequenceCodec, decodable_dataclass, ArrayCodec, ChoiceCodec, VectorCodec, DictionaryCodec

__all__ = [
    "Codable",
    "Codec", "EncodeError", "DecodeError", "BufferError",
    "GeneralCodec", "IntegerCodec",
    "BooleanCodec",
    "StringCodec",
    "ArrayCodec",
    "ChoiceCodec",
    "decodable_dataclass",
    "VectorCodec",
    "DictionaryCodec",
    "BitSequenceCodec",
    "JsonCodec", "JsonSerializable", "json_serializable"
]