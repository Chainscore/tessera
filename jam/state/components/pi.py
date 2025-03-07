from dataclasses import dataclass

from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.array import Array, decodable_array
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.constants import VALIDATOR_COUNT
from jam.utils.json import JsonSerde


@decodable_dataclass
@dataclass
class ValidatorStat(Codable, JsonSerde):
    blocks: U32
    tickets: U32
    pre_images: U32
    pre_images_size: U32
    guarantees: U32
    assurances: U32


@decodable_array(VALIDATOR_COUNT, ValidatorStat)
class AllValidatorStats(Array[ValidatorStat]):
    """All validator stats"""

    ...


@decodable_array(2, AllValidatorStats)
class Pi(Array[AllValidatorStats]):
    """Pi"""

    ...
