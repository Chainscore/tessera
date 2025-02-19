"""
Vector codec implementation for JAM.

Implements encoding and decoding of dynamic-length sequences according to the JAM specification.
Vectors are encoded with a length prefix followed by concatenated encoded elements.

Format:
    [Length_Tag: GeneralInt][Length_Data: varies][Elements...]

"""

from typing import TypeVar, Generic, List, Sequence, Union, Type

from jam.utils.codec.primitives.integers import GeneralCodec
from jam.utils.codec.utils import check_buffer_size
from jam.utils.codec.codec import Codec
from jam.utils.codec.errors import EncodeError, DecodeError
from jam.utils.codec.codable import Codable


T = TypeVar("T")


class VectorCodec(Codec[Sequence[Codable[T]]], Generic[T]):
    """
    Codec for dynamic-length sequences (vectors).

    Vectors are encoded with a variable-length prefix indicating size,
    followed by the concatenated encoded elements.
    """

    def encode_size(self, value: Sequence[Codable[T]]) -> int:
        """
        Calculate number of bytes needed to encode vector.

        Args:
            value: Sequence to encode

        Returns:
            Number of bytes needed

        Raises:
            EncodeError: If sequence is invalid type or too long
        """
        if not isinstance(value, Sequence):
            raise EncodeError(0, 0, f"Expected list or tuple, got {type(value)}")

        try:
            length_size = GeneralCodec().encode_size(len(value))
        except ValueError as e:
            raise EncodeError(0, 0, str(e))

        size = length_size
        for item in value:
            try:
                size += item.encode_size()
            except Exception as e:
                raise EncodeError(
                    0,
                    0,
                    f"Element {item} does not support encode_size(). Full error: {e}",
                )

        return size

    def encode_into(
        self, value: Sequence[Codable[T]], buffer: bytearray, offset: int = 0
    ) -> int:
        """
        Encode vector into buffer.

        Args:
            value: Sequence to encode
            buffer: Target buffer
            offset: Starting position in buffer

        Returns:
            Number of bytes written

        Raises:
            EncodeError: If sequence invalid or buffer too small
        """
        if not isinstance(value, Sequence):
            raise EncodeError(0, 0, f"Expected list or tuple, got {type(value)}")

        # Calculate total size and check buffer
        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)

        try:
            # Encode length prefix
            length_bytes = GeneralCodec().encode_into(len(value), buffer, offset)
            current_offset = offset + length_bytes

            # Encode elements
            # Ensure all elements are of the same type
            _element_type = None
            for item in value:
                if _element_type is None:
                    _element_type = type(item)
                elif type(item) != _element_type:
                    raise EncodeError(
                        0, 0, f"All elements must be of the same type, got {type(item)}"
                    )
                written = item.encode_into(buffer, current_offset)
                current_offset += written

            return current_offset - offset

        except ValueError as e:
            raise EncodeError(0, 0, str(e))

    @staticmethod
    def decode_from(
        codable_class: Type[Codable[T]],
        buffer: Union[bytes, bytearray, memoryview],
        offset: int = 0,
        max_length: int = 2**63 - 1,
    ) -> tuple[List[T], int]:
        """
        Decode vector from buffer.

        Args:
            buffer: Source buffer
            offset: Starting position in buffer

        Returns:
            Tuple of (decoded list, bytes read)

        Raises:
            DecodeError: If buffer too small or invalid encoding
        """
        try:
            # Decode length prefix
            length, length_size = GeneralCodec.decode_from(buffer, offset)
            current_offset = offset + length_size

            if length > max_length:
                length = max_length

            # Decode elements
            result = []
            for i in range(length):
                try:
                    item, size = codable_class.decode_from(buffer, current_offset)
                    result.append(item)
                    current_offset += size
                except DecodeError as e:
                    raise DecodeError(
                        0, 0, f"Failed to decode vector element {i}: {str(e)}"
                    )

            return result, current_offset - offset

        except DecodeError as e:
            raise DecodeError(0, 0, f"Failed to decode vector: {str(e)}")
