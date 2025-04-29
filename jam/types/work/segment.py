from jam.types.base.sequences.vector import decodable_vector, Vector
from jam.types.base.sequences.bytes.byte_array import decodable_bytearray, ByteArray

from jam.utils.constants import SEGMENT_SIZE


@decodable_bytearray(SEGMENT_SIZE)
class ByteArray4104(ByteArray):
    ...

Segment = ByteArray4104

@decodable_vector(Segment)
class Segments(Vector[Segment]):
    ...

@decodable_vector(Segments)
class MultiSegments(Vector[Segments]):
    ...