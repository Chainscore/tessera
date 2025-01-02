from typing import List, Optional, Self, Sequence, Tuple, Union

from jam.utils.codec.base import Codec, Codable
from jam.utils.codec.composite.bit_sequences import BitSequence, BitSequenceCodec
from jam.utils.constants import CORE_COUNT

class Bits(Codable, Sequence[BitSequence]):
    """Bit sequence codec."""
    def __init__(self, bits: Sequence[BitSequence]):
        super().__init__(BitSequenceCodec(len(bits)))
        self._bits = list(bits)

    def __new__(cls, bits: Sequence[BitSequence]) -> Self:
        return super().__new__(cls)
    
    def __len__(self) -> int:
        return len(self._bits)

    def __getitem__(self, index: Union[int, slice]) -> Union[BitSequence, Sequence[BitSequence]]:
        if isinstance(index, slice):
            return self._bits[index]
        else:
            if index < 0 or index >= len(self._bits):
                raise IndexError("Index out of range")
            return self._bits[index]

    def __setitem__(self, index: int, value: BitSequence) -> None:
        if index < 0 or index >= len(self._bits):
            raise IndexError("Index out of range")
        if not isinstance(value, BitSequence):
            raise TypeError("Value must be a BitSequence")
        self._bits[index] = value

    def __eq__(self, other: Sequence[BitSequence]) -> bool:
        if not isinstance(other, Bits):
            return Bits(other) == self
        if len(self._bits) != len(other._bits):
            return False
        return all(a == b for a, b in zip(self._bits, other._bits))

    def __repr__(self) -> str:
        return f"Bits(bits={self._bits})"

    @staticmethod
    def decode_from(
        bit_length: int,
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> Tuple[Sequence[BitSequence], int]:
        decoded_bits, size = BitSequenceCodec.decode_from(bit_length, buffer, offset)
        return decoded_bits, size
    
