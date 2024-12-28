"""
Core interfaces and base classes for codec.

This module defines the fundamental interfaces for encoding and decoding data types
in the JAM protocol. It provides abstract base classes that define the contract for
all codec implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Self, TypeVar, Generic, Tuple, Optional, Union, Any

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

class Codable(Generic[T]):
    """
    Codable interface.
    To be extended by any class that can be encoded/decoded.

    Args:
        codec: The codec to use for encoding/decoding.

    """
    def __init__(self, codec: Codec[Any]):
        self.codec = codec

    def encode_size(self) -> int:
        return self.codec.encode_size(self)

    def encode(self) -> bytes:
        return self.codec.encode(self)

    @staticmethod
    @abstractmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
        """
        Decode the value from the provided buffer starting at the specified offset.

        Args:
            buffer: The buffer to decode from
            offset: Starting position in the buffer

        Returns:
            Tuple containing:
                - The decoded value
                - Number of bytes read
        """
        pass
    
    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        """
        Encode the value into the provided buffer at the specified offset.

        Args:
            buffer: The buffer to encode into
            offset: Starting position in the buffer
            
        Returns:
            int: Number of bytes written
        """
        return self.codec.encode_into(self, buffer, offset)
    