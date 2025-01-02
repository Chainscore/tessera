from types import NoneType
from typing import Any, Optional, Tuple, Type, TypeVar, Union
from jam.types.base.null import Null
from jam.utils.codec.base import Codable
from jam.utils.codec.composite import ChoiceCodec

T = TypeVar('T', bound='Codable')

class Option(Codable):
    """
    An optional value.
    """
    def __init__(self, type: Type[T], value: Optional[Codable] = Null()):
        self.codec = ChoiceCodec([Null, type])
        self.value = value
    
    def __repr__(self):
        return f"{self.value}"
    
    @staticmethod
    def decode_from(type: Type[T], buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
        return ChoiceCodec.decode_from([Null, type], buffer, offset)
    
    def encode_size(self) -> int:
        if self.value is None:
            return 1
        return self.codec.encode_size(self.value)
    
    def encode(self) -> bytes:
        return self.codec.encode(self.value)
    
    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        if self.value is None:
            buffer[offset] = 0
            return 1
        return self.codec.encode_into(self.value, buffer, offset)
    
    def __eq__(self, other):
        if isinstance(other, Option):
            return self.value == other.value
        if isinstance(other, NoneType):
            return self.value == Null()
        return self.value == other
