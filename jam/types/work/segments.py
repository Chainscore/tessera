"""Work segment types for the JAM protocol."""

from tsrkit_types.dictionary import Dictionary
from tsrkit_types.sequences import TypedVector, TypedArray

from jam.types.protocol.core import SegmentRoot, WorkPackageHash
from jam.utils.constants import SEGMENT_SIZE


Segment = TypedArray[int, SEGMENT_SIZE]

Segments = TypedVector[Segment]

MultiSegments = TypedVector[Segments]

SegmentRootLookup = Dictionary[WorkPackageHash, SegmentRoot] 