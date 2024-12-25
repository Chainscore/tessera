from typing import List, Tuple, Union
from ..base import Codec, EncodeError, DecodeError
from ..utils import check_buffer_size, ensure_size

class BitSequenceCodec(Codec[List[int]]):
    """
    Codec for encoding and decoding sequences of bits.
    
    Bits are packed into octets (bytes) from least significant to most significant.
    """

    def encode_size(self, value: List[int]) -> int:
        # Calculate the number of bytes needed
        return (len(value) + 7) // 8

    def encode_into(self, value: List[int], buffer: bytearray, offset: int = 0) -> int:
        if not all(bit in (0, 1) for bit in value):
            raise EncodeError(0, 0, "Bit sequence must contain only 0s and 1s")

        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)

        byte = 0
        for i, bit in enumerate(value):
            byte |= (bit << (i % 8))
            if i % 8 == 7 or i == len(value) - 1:
                buffer[offset + i // 8] = byte
                byte = 0

        return total_size

    def decode_from(self, buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[List[int], int]:
        ensure_size(buffer, 1, offset)

        bits = []
        byte_index = 0
        while offset + byte_index < len(buffer):
            byte = buffer[offset + byte_index]
            for i in range(8):
                bits.append((byte >> i) & 1)
            byte_index += 1

        return bits, byte_index 