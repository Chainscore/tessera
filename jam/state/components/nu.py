from dataclasses import dataclass
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.work.report import WorkReport, WorkDependencies
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.constants import EPOCH_LENGTH
from jam.utils.jstruct import JsonSerde


@decodable_dataclass
@dataclass
class ReadyWR(Codable, JsonSerde):
    report: WorkReport
    dependencies: WorkDependencies


@decodable_vector(ReadyWR)
class AllReadyWRs(Vector[ReadyWR]):
    """All ready work reports"""

    ...


@decodable_array(EPOCH_LENGTH, AllReadyWRs)
class Nu(Array[AllReadyWRs]):
    """Nu"""

    ...
