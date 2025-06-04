from tsrkit_types.sequences import TypedVector, TypedArray
from jam.utils.constants import SEGMENT_SIZE


Segment = TypedArray[int, SEGMENT_SIZE]

Segments = TypedVector[Segment]

MultiSegments = TypedVector[Segments]