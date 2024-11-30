from typing import TypeVar
from jam.types.Codec import Codec

T = TypeVar('T', bound=Codec)

class Option(Codec[T]):
    """Option type: Could be Some(value) or None."""

    def __init__(self, value: T | None = None):
        self.value = value

    def encode(self) -> bytes:
        if self.value is None:
            return bytes([0x00])
        else:
            return bytes([0x01]) + self.encode()
