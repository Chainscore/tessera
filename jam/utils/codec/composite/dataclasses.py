
from dataclasses import fields, is_dataclass
from typing import Type, TypeVar, Tuple, Union

from jam.utils.codec.base import Codable
from .choices import ChoiceCodec

T = TypeVar('T')

def decodable_dataclass(cls: Type[T]) -> Type[T]:
    """
    Decorator that adds Codable support to any dataclass.
    """
    # Make the class inherit from Codable if it doesn't already
    if not issubclass(cls, Codable):
        cls.__bases__ = (Codable,) + cls.__bases__      

    def encode_size(self) -> int:
        size = 0
        for field in fields(self):
            item = getattr(self, field.name)
            # If this is an optional, we need to encode the value
            if field.type.__name__ == 'Optional':
                # If the item is None, we need to encode a 0
                size += 1
                if item is not None:
                    size += item.encode_size()
            else:
                size += item.encode_size()
        return size

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        # Must be a dataclass
        if not is_dataclass(self):
            raise TypeError(f"{self.__class__.__name__} must be a dataclass to use encoding")
        for field in fields(self):
            item = getattr(self, field.name)
            # If this is an optional, we need to encode the value
            if field.type.__name__ == 'Optional':
                # If the item is None, we need to encode a 0
                size = ChoiceCodec([type(None), field.type.__args__[0]]).encode_into(item, buffer, current_offset)
                current_offset += size
            else:
                size = item.encode_into(buffer, current_offset)
                current_offset += size

        return current_offset - offset
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[T, int]:
        current_offset = offset
        decoded_values = []
        for field in fields(cls): # type: ignore
            field_type = field.type
            
            # if this is an optional, we need to decode the field type
            # like it could be - typing.Optional[jam.types.header.EpochMark]
            if field_type.__name__ == 'Optional':
                # if the value is 0, we need to set the value to None
                print(f"Decoding optional field {field.name} with type {field_type}, {buffer[current_offset]}")
                value, size = ChoiceCodec.decode_from([type(None), field_type.__args__[0]], buffer, current_offset)
            else:
                value, size = field_type.decode_from(buffer, current_offset)
            decoded_values.append(value)
            current_offset += size
        
        instance = cls(*decoded_values)
        return instance, current_offset - offset  # type: ignore
    
    def __eq__(self, other: object) -> bool:
        # Compare all fields and values, return true if all are equal
        return all(getattr(self, field.name) == getattr(other, field.name) for field in fields(self))
    
    setattr(cls, '__eq__', __eq__)
    setattr(cls, 'encode_size', encode_size)
    setattr(cls, 'encode_into', encode_into)
    setattr(cls, 'decode_from', decode_from)
    return cls
