from typing import Generic, TypeVar

T = TypeVar('T')

class Codec(Generic[T]):
    """Base class for all codecs."""
    
    def encode(self, value: T) -> bytes:
        """Encode value into bytes."""
        return bytes()

    def decode(self, buffer: bytes):
        pass
