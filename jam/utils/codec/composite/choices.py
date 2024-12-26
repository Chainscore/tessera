"""
Choice codec implementation for JAM protocol.

Implements encoding and decoding of choice (union) values according to the JAM specification.
Choice values are encoded with a 1-byte tag followed by the encoded value based on the tag.
"""

from typing import TypeVar, Generic, Union, Type, Tuple, Dict
from ..base import Codec, EncodeError, DecodeError
from ..utils import check_buffer_size, ensure_size

T = TypeVar('T')

class ChoiceCodec(Codec[T], Generic[T]):
    """
    Codec for choice/union values.

    Choice values are encoded with a tag byte indicating the selected type,
    followed by the encoded value of that type.
    """

    def __init__(self, choices: Dict[int, Tuple[Type, Codec]]):
        """
        Initialize ChoiceCodec.

        Args:
            choices: A dictionary where keys are tag values (integers) and values
                     are tuples of (Type, Codec) for each choice.
        """
        self.choices = choices

    def encode_size(self, value: T) -> int:
        for tag, (choice_type, codec) in self.choices.items():
            if isinstance(value, choice_type):
                return 1 + codec.encode_size(value)  # 1 byte for tag
        raise EncodeError(0, 0, f"No matching choice found for type {type(value)}")

    def encode_into(self, value: T, buffer: bytearray, offset: int = 0) -> int:
        for tag, (choice_type, codec) in self.choices.items():
            if isinstance(value, choice_type):
                check_buffer_size(buffer, self.encode_size(value), offset)
                buffer[offset] = tag
                written = codec.encode_into(value, buffer, offset + 1)
                return 1 + written
        raise EncodeError(0, 0, f"No matching choice found for type {type(value)}")

    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[T, int]:
        ensure_size(buffer, 1, offset)
        tag = buffer[offset]
        if tag in self.choices:
            choice_type, codec = self.choices[tag]
            value, size = codec.decode_from(buffer, offset + 1)
            return value, 1 + size
        raise DecodeError(0, 0, f"Invalid choice tag: {tag}") 