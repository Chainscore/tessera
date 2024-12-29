from typing import Type, Union, Any, Optional, List, Tuple, Dict, Callable

from jam.utils.codec.base import Codable
from jam.utils.codec.composite.choices import ChoiceCodec

class Choice(Codable):
    """
    A choice is a value that can be one of several possible types.
    """
    def __init__(self, types: List[Type[Codable]]):
        self.codec = ChoiceCodec(types)
        if len(types) == 0:
            raise ValueError("Choice must have at least one type")
        self.types = types

    def set(self, value: Codable):
        # Make sure the value is in the list of types
        if type(value) not in self.types:
            raise ValueError(f"Value {value} is not in the list of types")
        # Set the value
        self.value = value

    def get(self) -> Codable:
        return self.value

    def encode_size(self) -> int:
        return self.codec.encode_size(self.value)
    
    def encode(self) -> bytes:
        buffer = bytearray(self.encode_size())
        self.encode_into(buffer)
        return buffer

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        return self.codec.encode_into(self.value, buffer, offset)

    @staticmethod
    def decode_from(types: List[Type[Codable]], buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
        return ChoiceCodec.decode_from(types, buffer, offset)