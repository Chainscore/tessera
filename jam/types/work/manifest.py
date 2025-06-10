"""Segment related types for the JAM protocol."""
from tsrkit_types import Uint, Dictionary, structure, Bytes, TypedVector, TypedArray

from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import WorkReportHash, ValidatorIndex, ExportsRoot

from jam.utils.constants import SEGMENT_SIZE

SegmentIndex = Uint[16]

Segment = TypedArray[int, SEGMENT_SIZE]
Segments = TypedVector[Segment]
MultiSegments = TypedVector[Segments]

SegmentDict = Dictionary[ExportsRoot, Segments]

@structure
class ProvedSegments:
    segment: Segments
    proof: Segments

Assurers = TypedVector[ValidatorIndex]

@structure
class ReportAssurers:
    report_hash: WorkReportHash
    assurers: Assurers

Extrinsic = Bytes

Extrinsics = TypedVector[Extrinsic]
MultiExtrinsics = TypedVector[Extrinsics]

Justification = TypedVector[OpaqueHash]
Justifications = TypedVector[Justification]
MultiJustifications = TypedVector[Justifications]