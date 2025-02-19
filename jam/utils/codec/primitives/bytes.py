"""Codec for byte sequences."""

from typing import Tuple, Union, Any

from jam.utils.codec.codec import Codec
from jam.utils.codec.primitives.integers import GeneralCodec


class BytesCodec(Codec):
    """Codec for variable-length byte sequences."""

    def encode_size(self, value: bytes) -> int:
        """Calculate encoded size of a byte sequence."""
        return GeneralCodec().encode_size(len(value)) + len(value)

    def encode_into(self, value: bytes, buffer: bytearray, offset: int = 0) -> int:
        """Encode a byte sequence into a buffer."""
        size = GeneralCodec().encode_into(len(value), buffer, offset)
        buffer[offset + size : offset + size + len(value)] = value
        return size + len(value)

    @staticmethod
    def decode_from(
        buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[bytes, int]:
        """Decode a byte sequence from a buffer."""
        length, size = GeneralCodec().decode_from(buffer, offset)
        data = buffer[offset + size : offset + size + length]
        return bytes(data), size + length


class FixedBytesCodec(Codec):
    """Codec for fixed-length byte sequences."""

    def __init__(self, size: int):
        """Initialize with fixed size."""
        self.size = size

    def encode_size(self, value: bytes) -> int:
        """Calculate encoded size of a byte sequence."""
        if len(value) != self.size:
            raise ValueError(f"Expected {self.size} bytes, got {len(value)}")
        return self.size

    def encode_into(self, value: bytes, buffer: bytearray, offset: int = 0) -> int:
        """Encode a byte sequence into a buffer."""
        if len(value) != self.size:
            raise ValueError(f"Expected {self.size} bytes, got {len(value)}")
        buffer[offset : offset + self.size] = value
        return self.size

    @staticmethod
    def decode_from(
        buffer: Union[bytes, bytearray, memoryview], offset: int = 0, size: int = 0
    ) -> Tuple[bytes, int]:
        """Decode a byte sequence from a buffer."""
        if len(buffer) - offset < size:
            raise ValueError(
                f"Buffer too small. Expected {size} bytes, got {len(buffer) - offset}"
            )
        data = buffer[offset : offset + size]
        return bytes(data), size
