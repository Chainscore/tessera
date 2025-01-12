"""
Core interfaces and base classes for codec.

This module defines the fundamental interfaces for encoding and decoding data types
in the JAM protocol. It provides abstract base classes that define the contract for
all codec implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields, is_dataclass
from typing import Type, TypeVar, Generic, Tuple, Optional, Union, Any, Dict

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
    
    Can be used in three ways:
    1. With a codec: Initialize with codec=some_codec
    2. With sequence: Initialize with enc_sequence=lambda: [field1, field2, ...]
    3. With JSON: Use to_json() and from_json() for JSON serialization
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
        
    def encode_size(self) -> int:
        """Calculate number of bytes needed to encode."""
        if self.codec is not None:
            return self.codec.encode_size(self.value if hasattr(self, 'value') else self)
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
        raise NotImplementedError("decode_from must be implemented by subclasses or added via decorator")

    @classmethod
    def from_json(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create an instance from a JSON dictionary.
        
        Args:
            data: Dictionary containing the serialized data
            
        Returns:
            An instance of the class
            
        Raises:
            ValueError: If the data is invalid or missing required fields
            TypeError: If the data contains invalid types
        """
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass to use JSON serialization")
            
        field_types = {f.name: f.type for f in fields(cls)}
        field_values = {}
        
        for field in fields(cls):
            name = field.name
            if name not in data:
                raise ValueError(f"Missing field {name}")
                
            value = data[name]
            field_type = field_types[name]
            
            # Handle nested Codable types
            if isinstance(field_type, type) and hasattr(field_type, 'from_json'):
                field_values[name] = field_type.from_json(value)
            else:
                field_values[name] = value
                
        return cls(**field_values)  # type: ignore

    def to_json(self) -> Dict[str, Any]:
        """Convert the instance to a JSON dictionary.
        
        Returns:
            Dictionary containing the serialized data
            
        Raises:
            TypeError: If the instance is not a dataclass
        """
        if not is_dataclass(self):
            raise TypeError(f"{self.__class__.__name__} must be a dataclass to use JSON serialization")
            
        result = {}
        for field in fields(self):
            value = getattr(self, field.name)
            
            # Handle nested types with to_json
            if hasattr(value, 'to_json'):
                result[field.name] = value.to_json()
            else:
                result[field.name] = value
                
        return result