from dataclasses import dataclass
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import WorkReportHash
from jam.types.work.report import WorkReport
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.constants import EPOCH_LENGTH


@decodable_dataclass
@dataclass
class ReadyWR(Codable):
    report: WorkReport
    dependencies: WorkReportHash


@decodable_vector(ReadyWR)
class AllReadyWRs(Vector[ReadyWR]):
    """All ready work reports"""

    ...


@decodable_array(EPOCH_LENGTH, AllReadyWRs)
class Nu(Array[AllReadyWRs]):
    """Nu"""

    ...
