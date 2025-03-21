from dataclasses import dataclass

from jam.types import Option
from jam.types.base import Choice
from jam.types.base.choices.option import decodable_option
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.protocol.core import TimeSlot
from jam.types.work.report import WorkReport
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.constants import CORE_COUNT
from jam.types.base.choices.option import Option
from jam.utils.json import JsonSerde


@decodable_dataclass
@dataclass
class WorkReportState(Codable, JsonSerde):
    """Work report state"""

    report: WorkReport
    timeout: TimeSlot


@decodable_option(WorkReportState)
class OptionalWorkReportState(Option):
    """Work report state"""
    ...


@decodable_array(CORE_COUNT, OptionalWorkReportState)
class Rho(Array[OptionalWorkReportState]):
    """Work report state array"""
    ...