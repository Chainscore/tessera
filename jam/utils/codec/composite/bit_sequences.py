from typing import Literal, Tuple, Union, Sequence

from jam.utils.byte_utils import ByteUtils
from ..primitives.integers import GeneralCodec
from ..codec import Codec
from ..errors import EncodeError
from ..utils import check_buffer_size, ensure_size


class BitSequenceCodec(Codec[Sequence[bool]]):
    """
    Codec for encoding and decoding sequences of bits.

    Bits are packed into octets (bytes) from least significant to most significant.
    IMP: It adds bit length encoded as a single byte at the beginning of the sequence ONLY if
    the bit length is not provided.

    If dynamic length sequence:
        - Initialise with None
        - No need to pass bit length to decode_from
    If fixed length sequence:
        - Initialise with bit length
        - Pass bit length to decode_from
    """

    _length: int | None = None
    _order: Literal["msb", "lsb"] = "msb"

    def __class_getitem__(cls, params):
        _len, _bo = None, "msb"
        if isinstance(params, tuple):
            _len, _bo = params
        else:
            if isinstance(params, int): _len = params
            else: _bo = params
        return type(cls.__class__.__name__, (cls,), {"_length": _len, "_order": _bo})

    def encode_size(self, value: Sequence[bool]) -> int:
        # Calculate the number of bytes needed
        bit_enc = 0
        if self._length is None:
            bit_enc = GeneralCodec().encode_size(len(value))

        return bit_enc + ((len(value) + 7) // 8)

    def encode_into(
        self, value: Sequence[bool], buffer: bytearray, offset: int = 0
    ) -> int:
        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)

        # Initialize all bytes to 0
        for i in range(0, total_size):
            buffer[offset + i] = 0

        if self._length is None:
            # Encode the bit length first
            offset += GeneralCodec().encode_into(len(value), buffer, offset)
        else:
            # Ensure bit length is size of value
            if len(value) != self._length:
                raise EncodeError(0, 0, "Bit sequence length mismatch")

        if not all(
            isinstance(bit, (bool, int)) and bit in (0, 1, True, False)
            for bit in value
        ):
            raise EncodeError(
                0,
                0,
                f"Bit sequence must contain only 0s and 1s, got an sequence of {value}",
            )

        buffer[offset : offset + total_size] = ByteUtils.bitarray_to_bytes(
            value, bitorder=self._order
        )

        return total_size

    @classmethod
    def decode_from(
        cls,
        buffer: Union[bytes, bytearray, memoryview],
        offset: int = 0,
    ) -> Tuple[Sequence[bool], int]:
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
        if cls._length is None:
            # Assume first byte is the bit length
            bit_length, size = GeneralCodec.decode_from(buffer, offset)
            offset += size

        if cls._length == 0:
            return [], 0

        # Calculate required bytes
        byte_count = (cls._length + 7) // 8
        ensure_size(buffer, byte_count, offset)

        result = ByteUtils.bytes_to_bitarray(
            buffer[offset : offset + byte_count], bitorder=cls._order
        )
        return [bool(bit) for i, bit in enumerate(result) if i < cls._length], byte_count
