from jam.types import ByteArray32
from jam.types.base.sequences.vector import decodable_vector, Vector
from jam.types.base.sequences.bytes.byte_array import decodable_bytearray, ByteArray
from jam.types.work.refine_context import OpaqueHashes
from jam.utils.constants import SEGMENT_SIZE
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from dataclasses import dataclass
from jam.types.protocol.core import OpaqueHash, ValidatorIndex


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

@dataclass
@decodable_dataclass
class SegmentsWithProof(Codable):
    segment: Segments
    proof: Segments

@decodable_vector(ValidatorIndex)
class Assurers(Vector[ValidatorIndex]):
    ...


@dataclass
@decodable_dataclass
class ErasureRootAssurers(Codable):
    erasure_root: OpaqueHash
    assurers: Assurers