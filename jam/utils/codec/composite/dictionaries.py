"""
Dictionary codec implementation for JAM protocol.

Implements encoding and decoding of key-value mappings according to the JAM specification.
Dictionaries are encoded as a length-prefixed sequence of key-value pairs, with pairs
sorted by encoded key bytes to ensure deterministic encoding.

Format:
    [Length_Tag: u8][Length_Data: varies][Pairs...]
    where each Pair is:
        [Encoded Key][Encoded Value]
"""

from typing import TypeVar, Generic, Dict as typing_Dict, Mapping, Union, Type, Tuple
from jam.utils.codec.primitives.integers import GeneralCodec
from jam.utils.codec.utils import check_buffer_size
from ..codec import Codec
from ..codable import Codable
from ..errors import EncodeError, DecodeError

K = TypeVar("K")
V = TypeVar("V")


class DictionaryCodec(Codec[Mapping[K, V]], Generic[K, V]):
    """
    Codec for key-value mappings.

    Dictionaries are encoded as length-prefixed sequences of key-value pairs,
    sorted by encoded key bytes for deterministic encoding.
    """

    def _encode_pair(
        self, key: Codable[K], value: Codable[V], buffer: bytearray, offset: int
    ) -> Tuple[bytes, int]:
        """
        Encode a single key-value pair into buffer.

        Args:
            key: Key to encode
            value: Value to encode
            buffer: Target buffer
            offset: Starting position in buffer

        Returns:
            Tuple of (key_bytes for sorting, bytes written)

        Raises:
            EncodeError: If key/value invalid or buffer too small
        """
        # Encode key
        if isinstance(key, tuple):
            key_bytes = b"".join([k.encode_into(buffer, offset) for k in key])
        else:
            key_bytes = key.encode_into(buffer, offset)

        if isinstance(value, list):  # Assuming list of Codable values
            value_bytes = b"".join([v.encode_into(buffer, offset) for v in value])
        else:
            value_bytes = value.encode_into(buffer, offset)

        return key_bytes + value_bytes, len(key_bytes + value_bytes)

    def encode_size(self, value: Mapping[Codable[K], Codable[V]]) -> int:
        """
        Calculate number of bytes needed to encode dictionary.

        Args:
            value: Dictionary to encode

        Returns:
            Number of bytes needed

        Raises:
            EncodeError: If dictionary contains invalid types
        """
        if not isinstance(value, (dict, Mapping)):
            raise EncodeError(
                0, 0, f"Expected dict or Mapping, got {type(value).__name__}"
            )

        # Calculate size for length prefix
        pairs = sorted(
            value.items(),
            key=lambda x: self._encode_pair(x[0], x[1], bytearray(1024), 0)[0],
        )

        # Calculate size for all pairs
        pairs_size = 0
        for k, v in pairs:
            try:
                pairs_size += k.encode_size() + v.encode_size()
            except AttributeError:
                raise EncodeError(
                    0,
                    0,
                    f"Expected Codable, got {type(k).__name__} or {type(v).__name__}",
                )

        # Get length prefix size from pair codec
        total_size = GeneralCodec().encode_size(len(pairs)) + pairs_size

        return total_size

    def encode_into(
        self, value: Mapping[Codable[K], Codable[V]], buffer: bytearray, offset: int = 0
    ) -> int:
        """
        Encode dictionary into buffer.

        Args:
            value: Dictionary to encode
            buffer: Target buffer
            offset: Starting position in buffer

        Returns:
            Number of bytes written

        Raises:
            EncodeError: If dictionary invalid or buffer too small
        """
        if not isinstance(value, (dict, Mapping)):
            raise EncodeError(
                0, 0, f"Expected dict or Mapping, got {type(value).__name__}"
            )

        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)

        try:
            # Get sorted pairs by encoded key
            temp_buffer = bytearray(1024)
            pairs_with_key_bytes = []

            for key, val in value.items():
                key_bytes, _ = self._encode_pair(key, val, temp_buffer, 0)
                pairs_with_key_bytes.append((key_bytes, (key, val)))

            pairs = [p[1] for p in sorted(pairs_with_key_bytes)]

            # Encode length prefix using VectorCodec's length encoding scheme
            len_encoded = GeneralCodec().encode(len(pairs))
            buffer[offset : offset + len(len_encoded)] = len_encoded
            current_offset = offset + len(len_encoded)

            # Encode each pair directly
            for key, val in pairs:
                try:
                    written = key.encode_into(buffer, current_offset)
                    current_offset += written
                    written = val.encode_into(buffer, current_offset)
                    current_offset += written
                except AttributeError:
                    raise EncodeError(
                        0,
                        0,
                        f"Expected Codable, got {type(key).__name__} or {type(val).__name__}",
                    )

            return current_offset - offset

        except EncodeError as e:
            raise EncodeError(0, 0, f"Failed to encode dictionary: {str(e)}")

    @staticmethod
    def decode_from(
        key_codable_class: Type[Codable[K]],
        value_codable_class: Type[Codable[V]],
        buffer: Union[bytes, bytearray, memoryview],
        offset: int = 0,
    ) -> Tuple[typing_Dict[K, V], int]:
        """
        Decode dictionary from buffer.

        Args:
            buffer: Source buffer
            offset: Starting position in buffer

        Returns:
            Tuple of (decoded dict, bytes read)

        Raises:
            DecodeError: If buffer too small or invalid encoding
        """
        try:
            # Decode length prefix using VectorCodec's length decoding scheme
            length, length_size = GeneralCodec.decode_from(buffer, offset)
            current_offset = offset + length_size

            # Decode pairs
            result = {}
            for _ in range(length):
                # Decode key
                key, key_size = key_codable_class.decode_from(buffer, current_offset)
                current_offset += key_size

                # Decode value
                value, value_size = value_codable_class.decode_from(
                    buffer, current_offset
                )
                current_offset += value_size

                if key in result:
                    raise DecodeError(0, 0, f"Duplicate key in dictionary: {key}")
                result[key] = value

            return result, current_offset - offset

        except DecodeError as e:
            raise DecodeError(0, 0, f"Failed to decode dictionary: {str(e)}")
