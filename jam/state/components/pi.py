
from dataclasses import dataclass

from jam.types.base.integers.general import Int
from jam.types.base.sequences.array import Array, decodable_array
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass
from jam.utils.constants import VALIDATOR_COUNT


@decodable_dataclass
@dataclass
class ValidatorStat(Codable):
    num_blocks: Int
    num_tickets: Int
    num_preimages: Int
    num_octets: Int
    num_reports: Int
    num_avail: Int


@decodable_array(VALIDATOR_COUNT, ValidatorStat)
class AllValidatorStats(Array[ValidatorStat]):
    """All validator stats"""
    ...

@decodable_array(2, AllValidatorStats)
class Pi(Array[AllValidatorStats]):
    """Pi"""
    ...