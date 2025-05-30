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
    length: int = 0

    def __class_getitem__(cls, _len: int):
        return type(cls.__class__.__name__, (cls,), {"length": _len})

    def encode_size(self, value: bytes) -> int:
        """Calculate encoded size of a byte sequence."""
        if len(value) != self.length:
            raise ValueError(f"Expected {self.length} bytes, got {len(value)}")
        return self.length

    def encode_into(self, value: bytes, buffer: bytearray, offset: int = 0) -> int:
        """Encode a byte sequence into a buffer."""
        if len(value) != self.length:
            raise ValueError(f"Expected {self.length} bytes, got {len(value)}")
        buffer[offset : offset + self.length] = value
        return self.length

    @classmethod
    def decode_from(
        cls, buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[bytes, int]:
        """Decode a byte sequence from a buffer."""
        if len(buffer) - offset < cls.length:
            raise ValueError(
                f"Buffer too small. Expected {cls.length} bytes, got {len(buffer) - offset}"
            )
        data = buffer[offset : offset + cls.length]
        return bytes(data), cls.length
