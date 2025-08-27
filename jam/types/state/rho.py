from tsrkit_types.sequences import TypedArray
from tsrkit_types.struct import structure
from tsrkit_types.option import Option
from jam.types.protocol.core import TimeSlot
from jam.types.work import WorkReport, WorkReports
from jam.utils.constants import CORE_COUNT


@structure
class WorkReportState:
    """Work report state"""

    report: WorkReport
    timeout: TimeSlot


OptionalWorkReportState = Option[WorkReportState]

# State key: 10
class Rho(TypedArray[OptionalWorkReportState, CORE_COUNT]):

    def pending_reps(self):
        pending_reports = WorkReports([])
        for state in self:
            data = state.unwrap()
            if isinstance(data, WorkReportState):
                pending_reports.append(data.report)

        return pending_reports