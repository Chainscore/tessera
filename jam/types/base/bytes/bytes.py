from typing import List, Union, Tuple, Any, ClassVar, Self

from jam.types.base.bytes.bits import Bits
from jam.utils.codec import Codable
from jam.utils.codec.primitives.bytes import BytesCodec, FixedBytesCodec
from jam.utils.json import JsonSerde


class Bytes(bytes, Codable, JsonSerde):

    _length: ClassVar[Union[None, int]] = None
    codec: ClassVar[Any] = BytesCodec()

    def __class_getitem__(cls, params):
        _len, _codec = None, BytesCodec()
        name = cls.__class__.__name__
        if params and params > 0:
            _len, _codec = params, FixedBytesCodec[params]()
            name = f"ByteArray{_len}"
        return type(name, (cls,), {
            "_length": _len,
            "codec": _codec
        })

    def __str__(self):
        return f"{self.__class__.__name__}({self.hex()})"

    @classmethod
    def from_bits(cls, bits: Bits, bit_order = "msb") -> Self:
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

    def to_bits(self, bit_order="msb") -> Bits:
        bits = []
        for byte in self:
            if bit_order == "msb":
                bits.extend([(byte >> i) & 1 for i in reversed(range(8))])
            elif bit_order == "lsb":
                bits.extend([(byte >> i) & 1 for i in range(8)])
            else:
                raise ValueError(f"Unknown bit_order: {bit_order}")
        return Bits(bits)