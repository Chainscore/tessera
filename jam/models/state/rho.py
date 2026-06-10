from tsrkit_types.sequences import TypedArray
from tsrkit_types.struct import structure
from tsrkit_types.option import Option
from jam.models.protocol.core import TimeSlot
from jam.models.work import WorkReport, WorkReports
from jam.models.work.guarantee import ReportGuarantee
from jam.utils.constants import CORE_COUNT


@structure
class WorkReportState:
    """Availability assignment for a core."""

    # WorkReportState -> Availability Assignment v0.8.0
    guarantee: ReportGuarantee
    timeout: TimeSlot

    @property
    def report(self) -> WorkReport:
        return self.guarantee.report


OptionalWorkReportState = Option[WorkReportState]

class Rho(TypedArray[OptionalWorkReportState, CORE_COUNT]):
    """
    Component: ρ
    Key: 10

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/131d02132d02?v=0.7.0
    """

    def pending_reps(self):
        pending_reports = WorkReports([])
        for state in self:
            data = state.unwrap()
            if isinstance(data, WorkReportState):
                pending_reports.append(data.report)

        return pending_reports