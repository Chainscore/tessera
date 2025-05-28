from typing import Union, Any, Tuple

from jam.types.base.integers.base import BaseInteger
from jam.utils.codec.codable import Codable
from jam.utils.codec.primitives.integers import GeneralCodec

class Int(BaseInteger, Codable):
    """
    General integer type
    This can hold integer < 2**64
    """

    codec = GeneralCodec()

    def __new__(cls, value: Any):
        if not 0 <= value < 2 ** 64:
            raise ValueError(f"Value must be between 0 and 2**64 - 1, got {value}")

        return super().__new__(cls, value)

    def encode_size(self) -> int:
        return self.codec.encode_size(self)

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        """Encode into provided buffer."""
        return self.codec.encode_into(
            self, buffer, offset
        )
