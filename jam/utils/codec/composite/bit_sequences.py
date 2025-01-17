from typing import Tuple, Union, Sequence

from jam.types.base.bit import Bit
from jam.utils.codec.primitives.integers import GeneralCodec
from ..base import Codec, EncodeError
from ..utils import check_buffer_size, ensure_size

class BitSequenceCodec(Codec[Sequence[Bit]]):
    """
    Codec for encoding and decoding sequences of bits.
    
    Bits are packed into octets (bytes) from least significant to most significant.
    """
    bit_length: int|None = None

    def __init__(self, bit_length: int|None = None):
        self.bit_length = bit_length

    def encode_size(self, value: Sequence[Bit]) -> int:
        # Calculate the number of bytes needed
        return (len(value) + 7) // 8

    def encode_into(self, value: Sequence[Bit], buffer: bytearray, offset: int = 0) -> int:
        print(f"Encoding bit sequence {value} of length {len(value)}")

        if self.bit_length is not None:
            if self.bit_length != len(value):
                raise EncodeError(
                    expected=self.bit_length,
                    actual=len(value),
                    message="Bit sequence length mismatch"
                )
            else:
                # Encode the bit length first
                offset += GeneralCodec().encode_into(self.bit_length, buffer, offset)

        if not all(bit in (0, 1, True, False) for bit in value):
            raise EncodeError(0, 0, "Bit sequence must contain only 0s and 1s")

        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)

        # Initialize all bytes to 0
        for i in range(total_size):
            buffer[offset + i] = 0

        # Pack bits from least significant to most significant
        for i, bit in enumerate(value):
            byte_index = offset + (i // 8)
            bit_position = i % 8
            if bool(bit):
                buffer[byte_index] |= (1 << bit_position)

        print(f"Encoded bit sequence {buffer[offset:offset+total_size]}")
        return total_size

    @staticmethod
    def decode_from(
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0,
        bit_length: int|None = None
    ) -> Tuple[Sequence[Bit], int]:
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
        if bit_length is None:
            # Assume first byte is the bit length
            bit_length, size = GeneralCodec.decode_from(buffer, offset)
            offset += size

        if bit_length == 0:
            return [], 0
            
        # Calculate required bytes
        byte_count = (bit_length + 7) // 8
        ensure_size(buffer, byte_count, offset)
        
        result = []
        for byte_idx in range(byte_count):
            byte = buffer[offset + byte_idx]
            for bit_idx in range(8):
                # Only append bits up to the requested length
                if len(result) < bit_length:
                    result.append(bool(byte & (1 << bit_idx)))
        
        print(f"Decoded bit sequence {result}")
        return result, byte_count