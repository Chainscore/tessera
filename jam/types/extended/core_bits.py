from typing import Union
from jam.types.base.bit_sequence import Bits
from jam.utils.constants import CORE_COUNT

class CoreBits(Bits):
    """Core bits type."""
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        return Bits.decode_from(CORE_COUNT, buffer, offset)
