"""Segment related types for the JAM protocol."""

from dataclasses import dataclass

from jam.types.base.dictionary import decodable_dictionary, Dictionary
from jam.types.base.integers import Int
from jam.types.base.sequences.vector import decodable_vector, Vector
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base.sequences.bytes.byte_array import decodable_bytearray, ByteArray
from jam.types.protocol.core import WorkReportHash, ValidatorIndex, ExportsRoot
from jam.types.work.refine_context import OpaqueHashes

from jam.utils.constants import SEGMENT_SIZE
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde


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

@decodable_dictionary(key_type=ExportsRoot, value_type=Segments)
class SegmentDict(Dictionary[ExportsRoot, Segments]):
    ...

@decodable_dataclass
@dataclass
class ProvedSegments(Codable, JsonSerde):
    segment: Segments
    proof: Segments

@decodable_vector(ValidatorIndex)
class Assurers(Vector[ValidatorIndex]):
    ...

@decodable_dataclass
@dataclass
class ReportAssurers(Codable, JsonSerde):
    report_hash: WorkReportHash
    assurers: Assurers

Extrinsic = Bytes

@decodable_vector(element_type=Extrinsic)
class Extrinsics(Vector[Extrinsic]):
    ...

@decodable_vector(element_type=Extrinsics)
class MultiExtrinsics(Vector[Extrinsics]):
    ...

@decodable_dataclass
@dataclass
class Justification(Codable, JsonSerde):
    length: Int
    justification: OpaqueHashes

@decodable_vector(element_type=Justification)
class Justifications(Vector[Justification]):
    ...

@decodable_vector(element_type=Justifications)
class MultiJustifications(Vector[Justifications]):
    ...