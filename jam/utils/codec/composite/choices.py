"""
Choice codec implementation for JAM protocol.

Implements encoding and decoding of choice (union) values according to the JAM specification.
Choice values are encoded with a 1-byte tag followed by the encoded value based on the tag.
"""

from typing import Sequence, TypeVar, Generic, Union, Type, Tuple, Optional, cast

from jam.utils.codec.primitives.integers import GeneralCodec
from ..base import Codable, Codec, EncodeError, DecodeError

T = TypeVar('T')

class ChoiceCodec(Codec[T], Generic[T]):
    """
    Codec for choice/union values.

    Choice values are encoded with a tag byte indicating the selected type,
    followed by the encoded value of that type.
    
    The tag is encoded as a general integer, followed by the encoded value
    of the selected type. The tag value corresponds to the index of the
    type in the choices list.
    
    Examples:
        >>> from jam.types.base.boolean import Boolean
        >>> from jam.types.base.integers import U8
        >>> codec = ChoiceCodec([Boolean, U8])
        >>> encoded = codec.encode(Boolean(True))
        >>> decoded, _ = codec.decode_from([Boolean, U8], encoded)
        >>> decoded == Boolean(True)
        True
    """

    def __init__(self, choices: Sequence[Type[Codable[T]]]):
        """
        Initialize ChoiceCodec.

        Args:
            choices: A list of types that are allowed for this choice. Their index
                    will be used as the tag.
                    
        Raises:
            ValueError: If choices list is empty
        """
        if len(choices) == 0:
            raise ValueError("Choices list cannot be empty")
            
        self.choices = choices
        self._tag_codec = GeneralCodec()

    def encode_size(self, value: Optional[Codable[T]]) -> int:
        """
        Calculate encoded size for value.
        
        Args:
            value: Value to encode
            
        Returns:
            Number of bytes needed for encoding
            
        Raises:
            EncodeError: If value type is not in choices list
        """
        if value is None:
            raise EncodeError(0, 0, "Cannot encode None value")
            
        if not (isinstance(value, Codable) or isinstance(value, type(None))):
            raise EncodeError(0, 0, "Value must be Codable")
            
        try:
            tag = self.choices.index(type(value))
        except ValueError:
            raise EncodeError(0, 0, f"Value type {type(value)} not in choices list")
            
        return self._tag_codec.encode_size(tag) + value.encode_size()

    def encode_into(self, value: Optional[Codable[T]], buffer: bytearray, offset: int = 0) -> int:
        """
        Encode value into buffer.
        
        Args:
            value: Value to encode
            buffer: Target buffer
            offset: Starting offset
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If value type is not in choices list or buffer is too small
        """
        if (not isinstance(value, Codable)) & (value is not None):
            raise EncodeError(0, 0, f"Value {value} must be Codable")
        
        try:
            tag = 0
            for i, choice in enumerate(self.choices):
                if choice is type(value):
                    tag = i
                    break
        except ValueError:
            raise EncodeError(0, 0, f"Value type {type(value)} not in choices list {self.choices}")
        
        tag_size = self._tag_codec.encode_into(tag, buffer, offset)
        offset += tag_size
        value_size = 0
        if value is not None:
            value_size = value.encode_into(buffer, offset)
            offset += value_size
        return tag_size + value_size

    @staticmethod
    def decode_from(
        choices: Sequence[Type[Codable[T]]], 
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> Tuple[Codable[T], int]:
        """
        Decode choice value from buffer.
        
        Args:
            choices: List of possible types
            buffer: Source buffer
            offset: Starting offset
            
        Returns:
            Tuple of (decoded value, bytes read)
            
        Raises:
            DecodeError: If buffer is invalid/too short or tag is invalid
            ValueError: If choices list is empty
        """
        if len(choices) == 0:
            raise ValueError("Choices list cannot be empty")
            
        tag_codec = GeneralCodec()
        tag, tag_size = tag_codec.decode_from(buffer, offset)
        
        if tag < 0 or tag >= len(choices):
            raise DecodeError(offset, 1, f"Invalid choice tag: {tag}")
        
        if choices[tag] is type(None):
            return None, tag_size
        
        value, value_size = choices[tag].decode_from(buffer, offset + tag_size)
        return cast(choices[tag], value), tag_size + value_size
