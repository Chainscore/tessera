from types import NoneType
from typing import Tuple, Union
from jam.utils.codec.base import Codable


class Null(Codable):
    """Null value."""
    value = None
    
    def __init__(self):
        pass
    
    def encode_size(self) -> int:
        return 0
    
    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        return 0

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[None, int]:
        return None, 0

    def get(self) -> None:
        return None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def __eq__(self, other):
        if isinstance(other, Null):
            return True
        return isinstance(other, NoneType)
