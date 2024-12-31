from typing import Tuple, Union
from jam.utils.codec.base import Codable


class Null(Codable):
    """Null value."""
    
    def encode_size(self) -> int:
        return 0
    
    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        return 0

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[None, int]:
        return None, 0
