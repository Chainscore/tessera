from dataclasses import dataclass
from jam.types.base import Choice, decodable_choice
from jam.types.base.null import Null
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.protocol.core import TimeSlot
from jam.types.work.report import WorkReport
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass
from jam.utils.constants import CORE_COUNT

@decodable_dataclass
@dataclass
class WorkReportState(Codable):
    """Work report state"""
    report: WorkReport
    time: TimeSlot

@decodable_choice([Null, WorkReportState])
class OptionalWorkReportState(Choice):
    """Work report state"""
    ...

@decodable_array(CORE_COUNT, OptionalWorkReportState)
class Rho(Array[OptionalWorkReportState]):
    """Work report state array"""
    ...
