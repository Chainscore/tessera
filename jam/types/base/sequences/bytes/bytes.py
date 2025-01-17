from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.base.utils.byte_utils import ByteUtils
from .byte import Bytable, Byte

@decodable_vector(Byte)
class Bytes(Vector[Byte]):
    """Variable-length byte sequence type."""
    def __init__(self, value: Bytable):
        """
        Initialize Bytes.
        
        Args:
            value: Bytable which is either int, bytes, str, bytearray, memoryview, Sequence[Byte]
        """
        data: list[Byte] = [Byte(b) for b in ByteUtils.to_bytes(value)]
        super().__init__(data)