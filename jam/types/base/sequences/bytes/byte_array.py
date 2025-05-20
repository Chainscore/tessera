from typing import Any, Callable, Sequence, Type, Literal
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.bytes.bit_array import Byte
from jam.utils.byte_utils import Bytable, ByteUtils
from copy import deepcopy

class ByteArray(Array[Byte]):
    """Array of bytes"""

    def __init__(self, value: Bytable):
        if (
            isinstance(value, Sequence)
            and len(value) > 0
            and isinstance(value[0], Byte)
        ):
            # Create a deepcopy instead of mutatable reference
            super().__init__(deepcopy(value))
        else:
            byt = [Byte(b) for b in ByteUtils.to_bytes(value)]
            super().__init__(byt)

    def __repr__(self) -> str:
        return f"0x{bytes(self).hex()}"

    def __int__(self) -> int:
        return int.from_bytes(bytes(self))

    def __hash__(self):
        return int(self)

    def to_int(self, byteorder: Literal["big", "little"] = "big"):
        return int.from_bytes(self, byteorder)

    @classmethod
    def from_json(cls, data: Any) -> "ByteArray":
        return cls(ByteUtils.to_bytes(data))

    def to_json(self) -> str:
        """Convert to JSON representation as hex string."""
        return f"0x{bytes(self).hex()}"


def decodable_bytearray(length: int) -> Callable[[Type[ByteArray]], Type[ByteArray]]:
    return decodable_array(length, Byte)


@decodable_bytearray(8)
class ByteArray8(ByteArray):
    ...


@decodable_bytearray(16)
class ByteArray16(ByteArray):
    ...


@decodable_bytearray(32)
class ByteArray32(ByteArray):
    ...


@decodable_bytearray(64)
class ByteArray64(ByteArray):
    ...


@decodable_bytearray(96)
class ByteArray96(ByteArray):
    ...


@decodable_bytearray(128)
class ByteArray128(ByteArray):
    ...


@decodable_bytearray(144)
class ByteArray144(ByteArray):
    ...


@decodable_bytearray(256)
class ByteArray256(ByteArray):
    ...


@decodable_bytearray(784)
class ByteArray784(ByteArray):
    ...