from typing import List, Union, Tuple, Any
from jam.types.base import Int
from jam.utils.codec import Codable
from jam.utils.json import JsonSerde

BitVector = List[int|bool]

class Bytes(bytes, Codable, JsonSerde):

    _length: None|Int = None

    def __str__(self):
        return f"{self.__class__.__name__}({self.hex()})"

    @classmethod
    def from_bits(cls, bits: BitVector, bit_order = "msb") -> "Bytes":
        # Sanitize input: make sure bits are 0 or 1
        bits = [int(bool(b)) for b in bits]
        n = len(bits)
        # Pad with zeros to multiple of 8
        pad = (8 - n % 8) % 8
        bits += [0] * pad

        byte_arr = []
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i + 8]
            if bit_order == "msb":
                # Most significant bit first
                val = 0
                for bit in byte_bits:
                    val = (val << 1) | bit
            elif bit_order == "lsb":
                # Least significant bit first
                val = 0
                for bit in reversed(byte_bits):
                    val = (val << 1) | bit
            else:
                raise ValueError(f"Unknown bit_order: {bit_order}")
            # noinspection PyUnreachableCode
            byte_arr.append(val)
        return cls(bytes(byte_arr))

    def to_bits(self, bit_order="msb") -> BitVector:
        bits = []
        for byte in self:
            if bit_order == "msb":
                bits.extend([(byte >> i) & 1 for i in reversed(range(8))])
            elif bit_order == "lsb":
                bits.extend([(byte >> i) & 1 for i in range(8)])
            else:
                raise ValueError(f"Unknown bit_order: {bit_order}")
        return bits

    def encode_size(self) -> int:
        return len(self)

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        """Encode a byte sequence into a buffer."""
        _len = self._length
        # Encode length if its a variable sequence bytes
        if not _len:
            _len = len(self)
            offset += Int(_len).encode_into(buffer, offset)

        # Handle case where if it is fixed len sequence and has insufficient elements
        if len(self) != _len:
            raise ValueError(f"Expected bytes to be of size {self._length}, got size {len(self)}")

        buffer[offset: offset + _len] = self
        return _len

    @classmethod
    def decode_from(
        cls, buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[Any, int]:
        _len = cls._length
        # Decode sequence length if variable length
        len_enc_size = 0
        if not _len:
            _len, len_enc_size = Int.decode_from(buffer, offset)
            offset+=len_enc_size

        data = buffer[offset:offset+_len]
        return cls(data), _len+len_enc_size
