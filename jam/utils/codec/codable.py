"""Base class for types that can encode/decode themselves."""

from typing import TypeVar, Generic, Tuple, Optional, Union, Any
from jam.utils.codec.codec import Codec

# Type variable for generic codec implementations
T = TypeVar("T")


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
        if isinstance(codec, Codec):
            self.codec = codec

    def encode_size(self) -> int:
        """Calculate number of bytes needed to encode."""
        if self.codec is not None:
            return self.codec.encode_size(self)
        raise NotImplementedError("No supported encoding method found")

    def encode(self) -> bytes:
        """Encode into bytes."""
        buffer = bytearray(self.encode_size())
        self.encode_into(buffer)
        return bytes(buffer)

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        """Encode into provided buffer."""
        if self.codec is not None:
            return self.codec.encode_into(self, buffer, offset)
        raise NotImplementedError("No supported encoding method found")

    @classmethod
    def decode_from(
        cls, buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[Any, int]:
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
        value, size = cls.codec.decode_from(buffer, offset)
        return cls(value), size
