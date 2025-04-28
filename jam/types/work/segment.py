from jam.types import ByteArray32
from jam.types.base.sequences.vector import decodable_vector, Vector
from jam.types.base.sequences.bytes.byte_array import decodable_bytearray, ByteArray

from jam.utils.constants import SEGMENT_SIZE


@decodable_bytearray(SEGMENT_SIZE)
class ByteArray4104(ByteArray):
    ...

Segment = ByteArray32

@decodable_vector(Segment)
class Segments(Vector[Segment]):
    ...