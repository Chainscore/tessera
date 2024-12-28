from typing import Self, Tuple, Union
from jam.utils.codec.base import Codable
from jam.utils.codec.primitives.bools import BooleanCodec

class Boolean(Codable, bytes):
    """
    Boolean type for JAM specification.
    """

    def __init__(self, value: bool):
        self.codec = BooleanCodec()

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        # decode and return a new Boolean instance
        value, size = BooleanCodec.decode_from(buffer, offset)
        return Boolean(value), size
