"""
Choice codec implementation for JAM protocol.

Implements encoding and decoding of choice (union) values according to the JAM specification.
Choice values are encoded with a 1-byte tag followed by the encoded value based on the tag.
"""

from typing import Sequence, TypeVar, Generic, Union, Type, Tuple, Dict

from jam.utils.codec.primitives.integers import GeneralCodec
from ..base import Codable, Codec, EncodeError, DecodeError

T = TypeVar('T')

class ChoiceCodec(Codec[T], Generic[T]):
    """
    Codec for choice/union values.

    Choice values are encoded with a tag byte indicating the selected type,
    followed by the encoded value of that type.
    """

    def __init__(self, choices: Sequence[Type[Codable[T]]]):
        """
        Initialize ChoiceCodec.

        Args:
            choices: A list of types that are allowed for this choice. Their index
                     will be used as the tag.
        """
        self.choices = choices

    def encode_size(self, value: Codable[T]) -> int:
        return GeneralCodec().encode_size(len(self.choices) - 1) + value.encode_size()

    def encode_into(self, value: Codable[T], buffer: bytearray, offset: int = 0) -> int:
        tag = self.choices.index(type(value))
        tag_size = GeneralCodec().encode_into(tag, buffer, offset)
        return tag_size + value.encode_into(buffer, offset + tag_size)

    @staticmethod
    def decode_from(choices: Sequence[Type[Codable[T]]], buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[T, int]:
        tag, tag_size = GeneralCodec.decode_from(buffer, offset)
        if tag < 0 or tag >= len(choices):
            raise DecodeError(0, 0, f"Invalid choice tag: {tag}")
        value, size = choices[tag].decode_from(buffer, offset + tag_size)
        return (value, tag_size + size)
