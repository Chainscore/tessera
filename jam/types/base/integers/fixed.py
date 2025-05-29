from typing import Any, Tuple, Union
from jam.types.base.integers.base import BaseInteger
from jam.utils.codec.codable import Codable
from jam.utils.codec.primitives.integers import IntegerCodec
from jam.utils.json import JsonSerde


class FixedInt(Codable, JsonSerde, BaseInteger):
    """Fixed-width integer type."""

    byte_size: int = 0  # override in subclasses
    has_sign: bool = False

    def __new__(cls, value: Any):
        value = int(value)
        if cls.byte_size > 0:
            bits = 8 * cls.byte_size
            half = bits // 2
            min_v = -(1 << (half - 1)) if cls.has_sign else 0
            max_v = (1 << (half - 1)) - 1 if cls.has_sign else (1 << bits) - 1
            if not (min_v <= value <= max_v):
                raise ValueError(f"{cls.__name__} out of range: {value!r} "
                                 f"not in [{min_v}, {max_v}]")

        return super().__new__(cls, value)

    # Serialization
    def encode_size(self) -> int:
        return self.byte_size

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        buffer[offset:offset+self.byte_size] = self.to_bytes(self.byte_size, "little")
        return self.byte_size

    @classmethod
    def decode_from(
            cls, buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[Any, int]:
        value, size = IntegerCodec(cls.byte_size).decode_from(cls.byte_size, buffer, offset)
        return cls.__new__(cls, value), size


class U8(FixedInt):
    byte_size = 1


class I8(FixedInt):
    byte_size = 1
    has_sign = True

class U16(FixedInt):
    byte_size = 2


class I16(FixedInt):
    byte_size = 2
    has_sign = True

class U32(FixedInt):
    byte_size = 4


class I32(FixedInt):
    byte_size = 4
    has_sign = True

class U64(FixedInt):
    byte_size = 8


class I64(FixedInt):
    byte_size = 8
    has_sign = True


class U128(FixedInt):
    byte_size = 16


class I128(FixedInt):
    byte_size = 16
    has_sign = True


class U256(FixedInt):
    byte_size = 32
