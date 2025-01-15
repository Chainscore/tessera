from typing import Literal, Sequence, Union
from .byte import Bytable, Byte
from jam.types.base.sequences.vector import Vector, decodable_vector

@decodable_vector(Byte)
class Bytes(Vector[Byte]):
    """Variable-length byte sequence type."""
    def __init__(self, value: Union[int, bytes, bytearray, memoryview, str, Sequence[Bytable]]):
        # Convert em all to Byte[]
        if isinstance(value, int):
            value = bytes([value])
        elif isinstance(value, bytes):
            value = bytearray(value)
        elif isinstance(value, bytearray):
            value = memoryview(value)
        elif isinstance(value, memoryview):
            value = value
        elif isinstance(value, Sequence):
            value = [Byte(b) for b in value]
        elif isinstance(value, str):
            if value.startswith('0x'):
                value = value[2:]
            value = bytes.fromhex(value)
        initial = [Byte(b) for b in value]
        super().__init__(initial)

    def __bytes__(self) -> bytes:
        return bytes(self.value for self in self)

    def hex(self) -> str:
        return bytes(self).hex()
