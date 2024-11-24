"""
Optional value codec implementation for JAM protocol.

Implements encoding and decoding of optional (nullable) values according to the JAM specification.
Optional values are encoded with a 1-byte tag followed by the encoded value if present.

Format:
    [Tag: u8][Value (if Some)]
    Tag = 0: None/null
    Tag = 1: Some/value present
"""

from typing import TypeVar, Generic, Optional, Union, Type, Tuple
from ..base import (
    Codec, CodecRegistry, EncodeError, DecodeError,
    check_buffer_size, ensure_size
)

T = TypeVar('T')

class OptionCodec(Codec[Optional[T]], Generic[T]):
    """
    Codec for optional/nullable values.
    
    Optional values are encoded with a tag byte indicating presence,
    followed by the encoded value if present.
    """
    
    # Constants for tag values
    TAG_NONE = 0
    TAG_SOME = 1
    TAG_SIZE = 1  # Size of tag in bytes
    
    def __init__(self, value_type: Type[T], value_codec: Optional[Codec[T]] = None):
        """
        Initialize option codec.
        
        Args:
            value_type: Type of the contained value
            value_codec: Optional specific codec for values. If None, will be 
                        looked up from registry
                        
        Raises:
            ValueError: If no codec is found for value_type
        """
        self.value_type = value_type
        
        # Get codec for values
        self.value_codec = value_codec or CodecRegistry.get(value_type)
        if self.value_codec is None:
            raise ValueError(
                f"No codec registered for value type {value_type.__name__}"
            )

    def encode_size(self, value: Optional[T]) -> int:
        """
        Calculate number of bytes needed to encode optional value.
        
        Args:
            value: Optional value to encode
            
        Returns:
            Number of bytes needed (1 for tag + value size if present)
        """
        if value is None:
            return self.TAG_SIZE
        return self.TAG_SIZE + self.value_codec.encode_size(value) # type: ignore

    def encode_into(self, value: Optional[T], buffer: bytearray, offset: int = 0) -> int:
        """
        Encode optional value into buffer.
        
        Args:
            value: Optional value to encode
            buffer: Target buffer
            offset: Starting position in buffer
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If buffer is too small or value is invalid type
        """
        if value is None:
            check_buffer_size(buffer, self.TAG_SIZE, offset)
            buffer[offset] = self.TAG_NONE
            return self.TAG_SIZE
            
        # Verify type if value is present
        if not isinstance(value, self.value_type):
            raise EncodeError(
                0, 0,
                f"Expected {self.value_type.__name__} or None, got {type(value)}"
            )
            
        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)
        
        # Write tag
        buffer[offset] = self.TAG_SOME
        
        # Write value
        written = self.value_codec.encode_into(value, buffer, offset + self.TAG_SIZE) # type: ignore
        return self.TAG_SIZE + written

    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], 
                   offset: int = 0) -> Tuple[Optional[T], int]:
        """
        Decode optional value from buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting position in buffer
            
        Returns:
            Tuple of (decoded value or None, bytes read)
            
        Raises:
            DecodeError: If buffer is too small or invalid encoding
        """
        ensure_size(buffer, self.TAG_SIZE, offset)
        
        tag = buffer[offset]
        if tag == self.TAG_NONE:
            return None, self.TAG_SIZE
            
        if tag == self.TAG_SOME:
            try:
                value, size = self.value_codec.decode_from( # type: ignore
                    buffer, offset + self.TAG_SIZE
                )
                return value, self.TAG_SIZE + size
            except DecodeError as e:
                raise DecodeError(0, 0, f"Failed to decode Some value: {str(e)}")
                
        raise DecodeError(
            0, 0,
            f"Invalid option tag: {tag}, expected 0 or 1"
        )


def make_option_codec(value_type: Type[T]) -> OptionCodec[T]:
    """
    Create option codec for given value type.
    
    Args:
        value_type: Type of values to encode/decode
        
    Returns:
        OptionCodec instance
        
    Raises:
        ValueError: If no codec found for value_type
    """
    return OptionCodec(value_type)


# Type alias helper for optional values
class Option(Generic[T]):
    """Type alias helper for optional values."""
    
    def __class_getitem__(cls, value_type: Type[T]) -> OptionCodec[T]:
        """
        Create option codec through type syntax.
        
        Example:
            codec = Option[int]  # Creates codec for Optional[int]
        """
        return make_option_codec(value_type)


# Register Option type with registry
from typing import _GenericAlias  # type: ignore
def register_option_type(option_type: _GenericAlias) -> None:
    """
    Register codec for an Optional[T] type.
    
    Args:
        option_type: Optional type to register (e.g., Optional[int])
    """
    if hasattr(option_type, "__origin__") and option_type.__origin__ is Union:
        # Extract the non-None type argument
        args = [arg for arg in option_type.__args__ if arg is not type(None)]
        if len(args) == 1:
            value_type = args[0]
            CodecRegistry.register(option_type, make_option_codec(value_type))