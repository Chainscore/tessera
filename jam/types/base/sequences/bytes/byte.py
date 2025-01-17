from typing import Literal
from jam.types import decodable_array, Array
from jam.types.base.bit import Bit
from jam.types.base.utils.byte_utils import Bytable, ByteUtils

@decodable_array(8, Bit)
class Byte(Array[Bit]):
    """
    A single byte value that supports codec operations. Array uses BitSequenceCodec.
    
    A Byte represents an 8-bit array that is encoded as
    a single byte.
    """

    def __init__(self, value: Bytable, bitorder: Literal["msb", "lsb"] = "msb"):
        """
        Initialize byte.
        
        Args:
            value: Bytable which is either int, bytes, str, bytearray, memoryview, U8, Sequence[0|1]
            bitorder: If "msb" (default), treats first bit as most significant.
                    If "lsb", treats first bit as least significant.
            
        Raises:
            TypeError: If value is not an integer
            ValueError: If value is out of range
        """
        data: list[bool] = ByteUtils.bytes_to_bitarray(ByteUtils.to_bytes(value), bitorder)
        self.value = [Bit(bit) for bit in data]