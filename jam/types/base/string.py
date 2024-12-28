from typing import Union
from jam.utils.codec.base import Codable
from jam.utils.codec.primitives.strings import StringCodec

class String(Codable, str):
    """
    String type for JAM specification.
    """
    
    def __init__(self, value: str):
        self.codec = StringCodec()

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        return StringCodec.decode_from(buffer, offset)
