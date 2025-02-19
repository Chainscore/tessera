from dataclasses import dataclass
from jam.types.base import Choice
from jam.types.base.choices.option import decodable_option
from jam.types.base.null import Null
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.protocol.core import TimeSlot
from jam.types.work.report import WorkReport
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.constants import CORE_COUNT


@decodable_dataclass
@dataclass
class WorkReportState(Codable):
    """Work report state"""

    report: WorkReport
    time: TimeSlot


@decodable_option(WorkReportState)
class OptionalWorkReportState(Choice):
    """Work report state"""

    ...


@decodable_array(CORE_COUNT, OptionalWorkReportState)
class Rho(Array[OptionalWorkReportState]):
    """Work report state array"""

    ...
