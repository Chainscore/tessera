"""
Choice codec implementation for JAM protocol.

Implements encoding and decoding of choice (union) values according to the JAM specification.
Choice values are encoded with a 1-byte tag followed by the encoded value based on the tag.
"""

from typing import Dict, TypeVar, Generic, Union, Type, Tuple

from jam.utils.codec.primitives.integers import GeneralCodec
from jam.utils.codec.codec import Codec
from jam.utils.codec.errors import EncodeError, DecodeError
from jam.utils.codec.codable import Codable

T = TypeVar("T")


class ChoiceCodec(Codec[T], Generic[T]):
    """
    Codec for choice/union values.

    Choice values are encoded with a tag byte indicating the selected type,
    followed by the encoded value of that type.

    The tag is encoded as a general integer, followed by the encoded value
    of the selected type. The tag value corresponds to the index of the
    type in the composite list.

    Args:
        choices: A list of types that are allowed for this choice. Their index
                will be used as the tag.
        tag_codec: A codec for the tag. Defaults to GeneralCodec() [Best for most cases].
                Alternatively we can use FixedInt(U8) for a fixed size tag if composite > 128.

    Raises:
        ValueError: If composite list is empty
    """

    _choices: Dict[str, Type[Codable[T]]]
    _tag_codec: Codec[int]

    def __init__(
        self,
        choices: Dict[str, Type[Codable[T]]],
        __tag_codec: Codec[int] = GeneralCodec(),
    ):
        """
        Initialize ChoiceCodec.

        Args:
            choices: A list of types that are allowed for this choice. Their index
                    will be used as the tag.

        Raises:
            ValueError: If composite list is empty
        """
        if len(choices) == 0:
            raise ValueError("Choices list cannot be empty")
        self._choices = choices
        self._tag_codec = __tag_codec

    def encode_size(self, _value: Dict[str, Codable[T]]) -> int:
        """
        Calculate encoded size for value.

        Args:
            value: Value to encode

        Returns:
            Number of bytes needed for encoding

        Raises:
            EncodeError: If value type is not in composite list
        """
        value_key = list(_value.keys())[0]
        value = _value[value_key]

        if value is None:
            raise EncodeError(0, 0, "Cannot encode None value")

        if not (isinstance(value, Codable) or isinstance(value, type(None))):
            raise EncodeError(0, 0, "Value must be Codable")

        try:
            tag = list(self._choices.keys()).index(value_key)
        except ValueError:
            raise EncodeError(0, 0, f"Value type {type(value)} not in composite list")

        return self._tag_codec.encode_size(tag) + value.encode_size()

    def encode_into(
        self, _value: Dict[str, Codable[T]], buffer: bytearray, offset: int = 0
    ) -> int:
        """
        Encode value into buffer.

        Args:
            value: Value to encode
            buffer: Target buffer
            offset: Starting offset

        Returns:
            Number of bytes written

        Raises:
            EncodeError: If value type is not in composite list or buffer is too small
        """
        value_key = list(_value.keys())[0]
        value = _value[value_key]

        if (not isinstance(value, Codable)) & (value is not None):
            raise EncodeError(0, 0, f"Value {value} must be Codable")

        tag = list(self._choices.keys()).index(value_key)

        tag_size = self._tag_codec.encode_into(tag, buffer, offset)
        offset += tag_size
        value_size = 0
        if value is not None:
            value_size = value.encode_into(buffer, offset)
            offset += value_size
        return tag_size + value_size

    @staticmethod
    def decode_from(
        choices: Dict[str, Type[Codable[T]]],
        buffer: Union[bytes, bytearray, memoryview],
        offset: int = 0,
    ) -> Tuple[Dict[str, Codable[T]], int]:
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
            ValueError: If composite list is empty
        """
        if len(choices) == 0:
            raise ValueError("Choices list cannot be empty")

        tag_codec = GeneralCodec()
        tag, tag_size = tag_codec.decode_from(buffer, offset)

        if tag < 0 or tag >= len(choices):
            raise DecodeError(offset, 1, f"Invalid choice tag: {tag}")

        choice_key = list(choices.keys())[tag]
        choice_type = list(choices.values())[tag]

        if choice_type is type(None):
            return {choice_key: None}, tag_size

        value, value_size = choice_type.decode_from(buffer, offset + tag_size)
        return {choice_key: value}, tag_size + value_size
