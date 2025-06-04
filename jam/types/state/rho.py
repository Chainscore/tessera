from tsrkit_types.sequences import TypedArray
from tsrkit_types.struct import structure
from tsrkit_types.option import Option
from jam.types.protocol.core import TimeSlot
# from jam.types.work.report import WorkReport  # Circular import issue
from jam.utils.constants import CORE_COUNT


@structure
class WorkReportState:
    """Work report state"""

    report: object  # WorkReport - temporarily using object to break circular import
    timeout: TimeSlot


OptionalWorkReportState = Option[WorkReportState]

Rho = TypedArray[OptionalWorkReportState, CORE_COUNT]