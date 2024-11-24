"""
Protocol support for JAM codecs.

This module provides support for encoding/decoding structured data types
using Python's dataclass and type annotation features.
"""

from typing import Type, TypeVar, get_type_hints
from dataclasses import is_dataclass, fields
import functools

from ..base import Codec, CodecRegistry, EncodeError, DecodeError

T = TypeVar('T')

class Protocol(Codec[T]):
    """
    Base class for protocol-based codecs.
    
    This provides automatic codec implementation based on type annotations
    and dataclass fields.
    """
    
    def __init__(self, protocol_class: Type[T]):
        """
        Initialize protocol codec.
        
        Args:
            protocol_class: Class to create codec for (must be a dataclass)
        """
        if not is_dataclass(protocol_class):
            raise ValueError(
                f"Protocol class {protocol_class.__name__} must be a dataclass"
            )
            
        self.protocol_class = protocol_class
        self.fields = fields(protocol_class)
        
        # Get codec for each field
        self.field_codecs = []
        for field in self.fields:
            codec = CodecRegistry.get(field.type)
            if codec is None:
                raise ValueError(
                    f"No codec registered for field {field.name} "
                    f"of type {field.type}"
                )
            self.field_codecs.append((field.name, codec))

    def encode_size(self, value: T) -> int:
        """Calculate encoded size of protocol value."""
        if not isinstance(value, self.protocol_class):
            raise EncodeError(
                0, 0,
                f"Expected {self.protocol_class.__name__}, got {type(value)}"
            )
            
        return sum(
            codec.encode_size(getattr(value, name))
            for name, codec in self.field_codecs
        )

    def encode_into(self, value: T, buffer: bytearray, offset: int = 0) -> int:
        """Encode protocol value into buffer."""
        if not isinstance(value, self.protocol_class):
            raise EncodeError(
                0, 0,
                f"Expected {self.protocol_class.__name__}, got {type(value)}"
            )
            
        current_offset = offset
        for name, codec in self.field_codecs:
            field_value = getattr(value, name)
            written = codec.encode_into(field_value, buffer, current_offset)
            current_offset += written
            
        return current_offset - offset

    def decode_from(self, buffer: bytes, offset: int = 0) -> tuple[T, int]:
        """Decode protocol value from buffer."""
        current_offset = offset
        field_values = {}
        
        try:
            for name, codec in self.field_codecs:
                value, size = codec.decode_from(buffer, current_offset)
                field_values[name] = value
                current_offset += size
                
            return self.protocol_class(**field_values), current_offset - offset
            
        except DecodeError as e:
            raise DecodeError(
                0, 0,
                f"Failed to decode {self.protocol_class.__name__}: {str(e)}"
            )


def codec_protocol(cls: Type[T]) -> Type[T]:
    """
    Decorator to create and register a codec for a protocol class.
    
    Args:
        cls: Class to create codec for (must be a dataclass)
        
    Returns:
        The class, unmodified but with registered codec
        
    Example:
        @codec_protocol
        @dataclass
        class Point:
            x: int
            y: int
    """
    codec = Protocol(cls)
    CodecRegistry.register(cls, codec)
    return cls