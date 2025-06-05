from tsrkit_types.integers import Uint
from tsrkit_types.sequences import TypedArray
from tsrkit_types.struct import structure
from tsrkit_types.option import Option

from jam.types.work import WorkReport
from jam.utils.constants import CORE_COUNT


@structure
class AvailabilityAssignment:
    """Availability assignment structure."""

    report: WorkReport
    timeout: Uint[32]


AvailabilityOption = Option[AvailabilityAssignment]

"""Fixed-size array of availability assignments."""
AvailabilityAssignments = TypedArray[AvailabilityOption, CORE_COUNT]
