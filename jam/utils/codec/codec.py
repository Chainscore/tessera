"""Codec interface for encoding and decoding data types."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Tuple, Union

# Type variable for generic codec implementations
T = TypeVar("T")


class Codec(ABC, Generic[T]):
    """Abstract base class defining the interface for encoding and decoding data."""

    @abstractmethod
    def encode_size(self, value: T) -> int:
        """Calculate the number of bytes needed to encode the value."""
        pass

    @abstractmethod
    def encode_into(self, value: T, buffer: bytearray, offset: int = 0) -> int:
        """Encode the value into the provided buffer at the specified offset."""
        pass

    def encode(self, value: T) -> bytes:
        """Encode the value into a new bytes object."""
        size = self.encode_size(value)
        buffer = bytearray(size)
        written = self.encode_into(value, buffer)
        return bytes(buffer[:written])

    @abstractmethod
    def decode_from(
        self, buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[T, int]:
        """Decode a value from the provided buffer starting at the specified offset."""
        pass
