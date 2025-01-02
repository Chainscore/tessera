from typing import Self, Tuple, Union
from jam.utils.codec.base import Codable
from jam.utils.codec.primitives.bools import BooleanCodec

class Boolean(Codable):
    """
    Boolean type for JAM specification.
    """
    def __init__(self, value: Union[bool, int, str]):
        if isinstance(value, bool):
            self.value = value
        elif isinstance(value, int):
            self.value = bool(value)
        elif isinstance(value, str):
            if value == "true" or value == "1" or value == "True" or value == "TRUE":
                self.value = True
            elif value == "false" or value == "0" or value == "False" or value == "FALSE":
                self.value = False
            else:
                raise ValueError(f"Invalid value for Boolean: {value}")
        else:
            raise ValueError(f"Invalid type for Boolean: {type(value)}")

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        return BooleanCodec().encode_into(self.value, buffer, offset)
    
    def encode(self) -> bytes:
        return BooleanCodec().encode(self.value)
    
    def encode_size(self) -> int:
        return BooleanCodec().encode_size(self.value)

    def __repr__(self):
        return f"Boolean({self.value})"

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Boolean):
            return self.value == value.value
        return False

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        # decode and return a new Boolean instance
        value, size = BooleanCodec.decode_from(buffer, offset)
        return Boolean(value), size
