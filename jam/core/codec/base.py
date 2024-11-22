"""
Core interfaces and base classes for JAM codec implementation.

This module defines the fundamental interfaces for encoding and decoding data types
in the JAM protocol. It provides abstract base classes that define the contract for
all codec implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic, Tuple, Optional, Union
import struct

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
    """
    Abstract base class defining the interface for encoding and decoding data.
    
    This class provides the core interface that all codec implementations must follow.
    It defines methods for calculating encoded size, encoding data into buffers,
    and decoding data from buffers.
    """
    
    @abstractmethod
    def encode_size(self, value: T) -> int:
        """
        Calculate the number of bytes needed to encode the value.
        
        Args:
            value: The value to be encoded
            
        Returns:
            int: Number of bytes required to encode the value
        """
        pass

    @abstractmethod
    def encode_into(self, value: T, buffer: bytearray, offset: int = 0) -> int:
        """
        Encode the value into the provided buffer at the specified offset.
        
        Args:
            value: The value to encode
            buffer: The buffer to encode into
            offset: Starting position in the buffer
            
        Returns:
            int: Number of bytes written
            
        Raises:
            EncodeError: If the buffer is too small or encoding fails
        """
        pass
    
    def encode(self, value: T) -> bytes:
        """
        Encode the value into a new bytes object.
        
        This is a convenience method that creates an appropriately sized buffer
        and encodes the value into it.
        
        Args:
            value: The value to encode
            
        Returns:
            bytes: The encoded value
            
        Raises:
            EncodeError: If encoding fails
        """
        size = self.encode_size(value)
        buffer = bytearray(size)
        written = self.encode_into(value, buffer)
        return bytes(buffer[:written])

    @abstractmethod
    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[T, int]:
        """
        Decode a value from the provided buffer starting at the specified offset.
        
        Args:
            buffer: The buffer to decode from
            offset: Starting position in the buffer
            
        Returns:
            Tuple containing:
                - The decoded value
                - Number of bytes read
                
        Raises:
            DecodeError: If the buffer is too small or decoding fails
        """
        pass

class CodecRegistry:
    """
    Registry for managing codec implementations.
    
    This class provides a central registry for mapping Python types to their codec
    implementations. It allows for registration of custom codecs and lookup of
    appropriate codecs for given types.
    """
    
    _codecs: dict[type, Codec] = {}
    
    @classmethod
    def register(cls, type_: type, codec: Codec) -> None:
        """
        Register a codec for a specific type.
        
        Args:
            type_: The Python type to register the codec for
            codec: The codec implementation
        """
        cls._codecs[type_] = codec
    
    @classmethod
    def get(cls, type_: type) -> Optional[Codec]:
        """
        Get the registered codec for a type.
        
        Args:
            type_: The Python type to get the codec for
            
        Returns:
            The registered codec or None if no codec is registered
        """
        return cls._codecs.get(type_)
    
    @classmethod
    def encode(cls, value: T) -> bytes:
        """
        Encode a value using its registered codec.
        
        Args:
            value: The value to encode
            
        Returns:
            The encoded bytes
            
        Raises:
            CodecError: If no codec is registered for the value's type
        """
        codec = cls.get(type(value))
        if codec is None:
            raise CodecError(f"No codec registered for type {type(value)}")
        return codec.encode(value)
    
    @classmethod
    def decode(cls, type_: type, buffer: Union[bytes, bytearray, memoryview]) -> Tuple[T, int]:
        """
        Decode a value using the registered codec for the specified type.
        
        Args:
            type_: The type to decode as
            buffer: The buffer to decode from
            
        Returns:
            Tuple containing:
                - The decoded value
                - Number of bytes read
                
        Raises:
            CodecError: If no codec is registered for the specified type
        """
        codec = cls.get(type_)
        if codec is None:
            raise CodecError(f"No codec registered for type {type_}")
        return codec.decode_from(buffer)

# Common utility functions used by codec implementations
def check_buffer_size(buffer: Union[bytes, bytearray, memoryview], expected: int, offset: int = 0) -> None:
    """
    Check if a buffer has enough remaining space.
    
    Args:
        buffer: The buffer to check
        expected: The number of bytes needed
        offset: Starting position in the buffer
        
    Raises:
        EncodeError: If the buffer is too small
    """
    available = len(buffer) - offset
    if available < expected:
        raise EncodeError(expected, available, "Buffer too small")

def ensure_size(buffer: Union[bytes, bytearray, memoryview], expected: int, offset: int = 0) -> None:
    """
    Ensure a buffer has enough bytes available for reading.
    
    Args:
        buffer: The buffer to check
        expected: The number of bytes needed
        offset: Starting position in the buffer
        
    Raises:
        DecodeError: If the buffer is too small
    """
    available = len(buffer) - offset
    if available < expected:
        raise DecodeError(expected, available, "Insufficient bytes in buffer")