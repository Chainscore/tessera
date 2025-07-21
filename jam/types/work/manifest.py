"""Segment related types for the JAM protocol."""
from tsrkit_types import Dictionary, structure, Bytes, TypedVector, TypedArray, U8, U16

from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import SegmentRoot, WorkPackageHash
from jam.types.protocol.core import WorkReportHash, ValidatorIndex, ExportsRoot

from jam.utils.constants import SEGMENT_SIZE

SegmentIndex = U16

Segment = Bytes[SEGMENT_SIZE]
Segments = TypedVector[Segment]
MultiSegments = TypedVector[Segments]

SegmentDict = Dictionary[ExportsRoot, Segments]
SegmentRootLookup = Dictionary[
    WorkPackageHash, SegmentRoot, "work_package_hash", "segment_tree_root"
]


@structure
class ProvedSegments:
    segment: Segments
    proof: Segments

    def __len__(self):
        return len(self.segment) + len(self.proof)


Assurers = TypedVector[ValidatorIndex]


@structure
class ReportAssurers:
    report_hash: WorkReportHash
    assurers: Assurers


Extrinsic = Bytes

Extrinsics = TypedVector[Extrinsic]
MultiExtrinsics = TypedVector[Extrinsics]

Justification = TypedVector[Bytes]
Justifications = TypedVector[Justification]
MultiJustifications = TypedVector[Justifications]
