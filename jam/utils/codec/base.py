"""
Core interfaces and base classes for codec.

This module defines the fundamental interfaces for encoding and decoding data types
in the JAM protocol. It provides abstract base classes that define the contract for
all codec implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from typing import Type, Self, TypeVar, Generic, Tuple, Optional, Union, Any, Sequence, Callable

# Type variable for generic codec implementations
T = TypeVar('T')

class CodecError(Exception):
    """Base class for codec-related exceptions."""
    pass

@dataclass
class BufferError(CodecError):
    """Exception raised for buffer-related errors."""
    expected: int
    actual: int
    message: str = "Buffer error"

    def __str__(self) -> str:
        return f"{self.message}: expected {self.expected} bytes, got {self.actual}"

class EncodeError(BufferError):
    """Exception raised when encoding fails."""
    pass

class DecodeError(BufferError):
    """Exception raised when decoding fails."""
    pass

class Codec(ABC, Generic[T]):
    """Abstract base class defining the interface for encoding and decoding data."""
    
    @abstractmethod
    def encode_size(self, value: T) -> int:
        """Calculate the number of bytes needed to encode the value."""
        pass

    @abstractmethod
    def encode_into(self, value: T, buffer: bytearray, offset: int = 0) -> int:
        """Encode the value into the provided buffer at the specified offset."""
        pass
    
    def encode(self, value: T) -> bytes:
        """Encode the value into a new bytes object."""
        size = self.encode_size(value)
        buffer = bytearray(size)
        written = self.encode_into(value, buffer)
        return bytes(buffer[:written])

    @abstractmethod
    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[T, int]:
        """Decode a value from the provided buffer starting at the specified offset."""
        pass

class Codable(Generic[T]):
    """
    Base class for all codable types.
    
    Can be used in two ways:
    1. With a codec: Initialize with codec=some_codec
    2. With sequence: Initialize with enc_sequence=lambda: [field1, field2, ...]
    """
    
    value: Any = None
    codec: Optional[Codec[Any]] = None
    
    def __init__(self, codec: Optional[Codec[Any]] = None):
        """
        Initialize the Codable.
        
        Args:
            codec: Optional codec to use for encoding/decoding
            enc_sequence: Optional function that returns sequence of fields to encode
        """
        self.codec = codec
        
    def enc_sequence(self) -> Sequence[Self]: ...

    def encode_size(self) -> int:
        """Calculate number of bytes needed to encode."""
        if self.codec is not None:
            return self.codec.encode_size(self.value if hasattr(self, 'value') else self)
        elif self.enc_sequence is not None:
            return sum(item.encode_size() for item in self.enc_sequence())
        raise NotImplementedError("No supported encoding method found")

    def encode(self) -> bytes:
        """Encode into bytes."""
        buffer = bytearray(self.encode_size())
        self.encode_into(buffer)
        return bytes(buffer)

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        """Encode into provided buffer."""
        if self.codec is not None:
            return self.codec.encode_into(
                self.value if hasattr(self, 'value') else self,
                buffer, 
                offset
            )
        elif self.enc_sequence is not None:
            current_offset = offset
            for item in self.enc_sequence():
                size = item.encode_into(buffer, current_offset)
                current_offset += size
            return current_offset - offset
        raise NotImplementedError("No supported encoding method found")

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
        """
        Decode from buffer. Must be implemented by subclasses or added via decorator.
        
        Args:
            buffer: Buffer to decode from
            offset: Starting position in buffer
            
        Returns:
            Tuple containing:
                - The decoded value
                - Number of bytes read
        """
        # We cannot implement this here because this is static method and we need to know
        # the codec to decode it.
        raise NotImplementedError("decode_from must be implemented by subclasses or added via decorator")




def codable_dataclass() -> Callable[[Type[T]], Type[T]]:
    """
    Decorator that adds Codable support to any dataclass.
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Make the class inherit from Codable if it doesn't already
        if not issubclass(cls, Codable):
            cls.__bases__ = (Codable,) + cls.__bases__
            
        def enc_sequence(self) -> Sequence[Codable]:
            return [getattr(self, field.name) for field in fields(self)]
        
        @staticmethod
        def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[T, int]:
            current_offset = offset
            decoded_values = []
            
            for field in fields(cls): # type: ignore
                field_type = field.type
                if isinstance(field_type, str):
                    raise ValueError(f"Field type '{field_type}' is not resolved")
                value, size = field_type.decode_from(buffer, current_offset)
                decoded_values.append(value)
                current_offset += size
                
            instance = cls(*decoded_values)
            return instance, current_offset - offset  # type: ignore
        
        setattr(cls, 'enc_sequence', enc_sequence)
        setattr(cls, 'decode_from', decode_from)
        return cls
    
    return decorator