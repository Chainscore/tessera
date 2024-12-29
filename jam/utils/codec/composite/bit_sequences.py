from typing import List, Tuple, Union, Sequence
from ..base import Codec, EncodeError, DecodeError
from ..utils import check_buffer_size, ensure_size

BitSequence = Union[bool, int]

class BitSequenceCodec(Codec[Sequence[BitSequence]]):
    """
    Codec for encoding and decoding sequences of bits.
    
    Bits are packed into octets (bytes) from least significant to most significant.
    """

    def __init__(self, bit_length: int):
        self.bit_length = bit_length

    def encode_size(self, value: Sequence[BitSequence]) -> int:
        # Calculate the number of bytes needed
        return (len(value) + 7) // 8

    def encode_into(self, value: Sequence[BitSequence], buffer: bytearray, offset: int = 0) -> int:
        if self.bit_length != len(value):
            raise EncodeError(
                expected=self.bit_length,
                actual=len(value),
                message="Bit sequence length mismatch"
            )

        if not all(bit in (0, 1, True, False) for bit in value):
            raise EncodeError(0, 0, "Bit sequence must contain only 0s and 1s")

        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)

        byte = 0
        for i, bit in enumerate(value):
            byte |= (bool(bit) << (i % 8))
            if i % 8 == 7 or i == len(value) - 1:
                buffer[offset + i // 8] = byte
                byte = 0

        return total_size

    @staticmethod
    def decode_from(length: int,
                    buffer: Union[bytes, bytearray, memoryview], 
                    offset: int = 0) -> Tuple[Sequence[BitSequence], int]:
        """
        Decode bit sequence from buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting offset
            bit_length: Expected number of bits (required)
            
        Returns:
            Tuple of (decoded bit list, bytes read)
            
        Raises:
            DecodeError: If buffer too small or bit_length not specified
        """
        if length is None:
            raise DecodeError(
                expected=0,
                actual=0,
                message="bit_length must be specified for decoding"
            )
        
        if length == 0:
            return [], 0
            
        # Calculate required bytes
        byte_count = (length + 7) // 8
        ensure_size(buffer, byte_count, offset)
        
        result = []
        for byte_idx in range(byte_count):
            byte = buffer[offset + byte_idx]
            for bit_idx in range(8):
                # Only append bits up to the requested length
                if len(result) < length:
                    result.append(bool(byte & (1 << bit_idx)))
            
        return result, byte_count