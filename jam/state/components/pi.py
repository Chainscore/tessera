from dataclasses import dataclass

from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.integers.fixed import U16, U32
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.protocol.core import Gas, ServiceId
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.constants import CORE_COUNT, VALIDATOR_COUNT
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


@decodable_dataclass
@dataclass
class CoreStat(Codable, JsonSerde):
    gas_used: U32
    imports: U32
    extrinsic_count: U32
    extrinsic_size: U32
    exports: U32
    bundle_size: U32
    da_load: U32
    popularity: U32


@decodable_dataclass
@dataclass
class ServiceStat(Codable, JsonSerde):
    provided_count: U16
    provided_size: U32
    refinement_count: U32
    refinement_gas_used: Gas
    imports: U32
    exports: U32
    extrinsic_size: U32
    extrinsic_count: U32
    accumulate_count: U32
    accumulate_gas_used: Gas
    on_transfers_count: U32
    on_transfers_gas_used: Gas


@decodable_array(VALIDATOR_COUNT, ValidatorStat)
class AllValidatorStats(Array[ValidatorStat]):
    """All validator stats"""

    ...


@decodable_array(CORE_COUNT, CoreStat)
class AllCoreStats(Array[CoreStat]):
    """All core stats"""

    ...


@decodable_dictionary(ServiceId, ServiceStat)
class AllServiceStats(Dictionary[ServiceId, ServiceStat]):
    """All service stats"""

    ...


@decodable_array(
    4, (AllValidatorStats, AllValidatorStats, AllCoreStats, AllServiceStats)
)
class Pi(Array):
    """Pi"""

    ...
