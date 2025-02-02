from enum import Enum as OGEnum
from typing import Tuple, Type, Union
from jam.types.base.integers.fixed import U8
from jam.utils.codec.codable import Codable

class Enum(Codable, OGEnum):
    """Decodable Enum type - Extending the built-in Enum type to add encoding and decoding methods

    How to use it:
    >>> class MyEnum(Enum):
    >>>     A = 1
    >>>     B = 2
    >>>     C = 3
    >>> 
    >>> value = MyEnum.A
    >>> encoded = value.encode()
    >>> decoded, bytes_read = MyEnum.decodeFrom(encoded)
    >>> assert decoded == value
    >>> assert bytes_read == 1
    >>> 
    >>> assert MyEnum.from_json(1) == MyEnum.A
    >>> assert MyEnum.from_json("A") == MyEnum.A
    """
    
    def encode_size(self) -> int:
        return 1
    
    def encode_into(self, buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> bytes:
        # Get the index of the enum value in all enums
        # Encode the index as a byte
        all_enums = self.__class__._member_names_
        index = all_enums.index(self.name)
        if index > 255:
            raise ValueError("Enum index is too large to encode into a single byte")
        return U8(index).encode_into(buffer, offset)

    @classmethod
    def decodeFrom(cls, data: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple['Enum']:
        # Decode the byte (index of enum) into an JamEnum
        # Return the enum value
        index, bytes_read = U8.decode_from(data, offset)
        return cls._member_map_[cls._member_names_[index]], bytes_read
    
    @classmethod
    def from_json(cls, value) -> 'Enum':
        for v in cls.__members__.values():
            if v._value_ == value or v._name_ == value:
                return v
        raise ValueError(f"Invalid value: {value}")
    
    def to_json(self) -> dict:
        return {"name": self.name}
    
def decodable_enum(cls: Type[Enum]) -> Type[Enum]:
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Enum, int]:
        return cls.decodeFrom(buffer, offset)

    cls.decode_from = decode_from
    return cls