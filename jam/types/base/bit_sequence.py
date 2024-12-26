from typing import List, Optional, Sequence, Tuple, Union

from jam.utils.codec.base import Codec, Codable
from jam.utils.codec.composite.bitsequence import BitSequence, BitSequenceCodec
from jam.utils.constants import CORE_COUNT

class Bits(Codable, Sequence[bool]):
    """Bit sequence codec."""
    def __init__(self, bit_length: int, bits: Optional[Sequence[bool]] = None):
        if bit_length <= 0:
            raise ValueError("Bit length must be greater than 0")
        self.bit_length = bit_length
        self.codec = BitSequenceCodec(bit_length)
        if bits is not None:
            if len(bits) != bit_length:
                raise ValueError(f"Expected {bit_length} bits, got {len(bits)}")
            self._bits = list(bits)
        else:
            self._bits = [False] * bit_length

    def __len__(self) -> int:
        return self.bit_length

    def __getitem__(self, index: Union[int, slice]) -> Union[bool, Sequence[bool]]:
        if isinstance(index, slice):
            return self._bits[index]
        else:
            if index < 0 or index >= self.bit_length:
                raise IndexError("Index out of range")
            return self._bits[index]

    def __setitem__(self, index: int, value: bool) -> None:
        if index < 0 or index >= self.bit_length:
            raise IndexError("Index out of range")
        if not isinstance(value, bool):
            raise TypeError("Value must be a boolean")
        self._bits[index] = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bits):
            return False
        return self.bit_length == other.bit_length and self._bits == other._bits

    def __repr__(self) -> str:
        return f"Bits(bit_length={self.bit_length}, bits={self._bits})"

    def encode_size(self) -> int:
        return self.codec.encode_size(self._bits)

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        return self.codec.encode_into(self._bits, buffer, offset)

    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Sequence[BitSequence], int]:
        decoded_bits, size = self.codec.decode_from(buffer, offset)
        return decoded_bits, size

class CoreBits(Bits):
    """Core bits codec."""
    def __init__(self, bits: Optional[Sequence[bool]] = None):
        super().__init__(CORE_COUNT, bits)