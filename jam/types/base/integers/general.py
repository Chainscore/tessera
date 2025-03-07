from typing import Union, Any, Tuple, TypeVar
from jam.utils.codec.codable import Codable
from jam.utils.codec.primitives.integers import GeneralCodec
from .base import BaseInteger

T = TypeVar("T", bound="BaseInteger")


# General integer type
class Int(BaseInteger, Codable):
    def __init__(self, value: Union[int, "BaseInteger"]):
        super().__init__(value)
        self._validate(self.value)
        self.codec = GeneralCodec()

    def _validate(self, value: int) -> None:
        """Validate the integer value is within bounds."""
        if not 0 <= value <= 2**64 - 1:
            raise ValueError(f"Value must be between 0 and 2**64 - 1, got {value}")

    @staticmethod
    def decode_from(
        buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[Any, int]:
        value, size = GeneralCodec().decode_from(buffer, offset)
        return Int(value), size
