from dataclasses import dataclass

from jam.types.base import Vector, decodable_vector, Int
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

    @staticmethod
    def empty() -> "ValidatorStat":
        return ValidatorStat.from_json({"blocks": 0, "tickets": 0, "pre_images": 0, "pre_images_size": 0, "guarantees": 0, "assurances": 0})


@decodable_dataclass
@dataclass
class CoreStat(Codable, JsonSerde):
    da_load: Int
    popularity: Int
    imports: Int
    exports: Int
    extrinsic_size: Int
    extrinsic_count: Int
    bundle_size: Int
    gas_used: Int

    @staticmethod
    def empty() -> "CoreStat":
        return CoreStat(gas_used=Int(0), imports=Int(0), extrinsic_count=Int(0), extrinsic_size=Int(0), exports=Int(0), bundle_size=Int(0), da_load=Int(0), popularity=Int(0))


@decodable_dataclass
@dataclass
class ServiceStat(Codable, JsonSerde):
    provided_count: Int
    provided_size: Int
    refinement_count: Int
    refinement_gas_used: Int
    imports: Int
    exports: Int
    extrinsic_size: Int
    extrinsic_count: Int
    accumulate_count: Int
    accumulate_gas_used: Int
    on_transfers_count: Int
    on_transfers_gas_used: Int

    @staticmethod
    def empty() -> "ServiceStat":
        return ServiceStat.from_json({
            "provided_count": 0,
            "provided_size": 0,
            "refinement_count": 0,
            "refinement_gas_used": 0,
            "imports": 0,
            "exports": 0,
            "extrinsic_size": 0,
            "extrinsic_count": 0,
            "accumulate_count": 0,
            "accumulate_gas_used": 0,
            "on_transfers_count": 0,
            "on_transfers_gas_used": 0,
        })


@decodable_array(VALIDATOR_COUNT, ValidatorStat)
class AllValidatorStats(Array[ValidatorStat]):
    """All validator stats"""

    @staticmethod
    def empty() -> "AllValidatorStats":
        return AllValidatorStats([ValidatorStat.empty() for _ in range(VALIDATOR_COUNT)])


@decodable_array(CORE_COUNT, CoreStat)
class AllCoreStats(Array[CoreStat]):
    """All core stats"""

    @staticmethod
    def empty():
        return AllCoreStats([CoreStat.empty() for _ in range(CORE_COUNT)])


@decodable_dictionary(ServiceId, ServiceStat ,key_name="id", value_name="record")
class AllServiceStats(Dictionary[ServiceId, ServiceStat]):
    """All service stats"""

    ...


@decodable_dataclass
@dataclass
class Pi(Codable, JsonSerde):
    """Pi"""

    vals_current: AllValidatorStats
    vals_last: AllValidatorStats
    cores: AllCoreStats
    services: AllServiceStats
