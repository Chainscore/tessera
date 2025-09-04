from tsrkit_types.sequences import TypedArray
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.integers import Uint, U32
from tsrkit_types.struct import structure
from jam.types.protocol.core import ServiceId
from jam.utils.constants import CORE_COUNT, VALIDATOR_COUNT


@structure
class ValidatorStat:
    blocks: U32 # b
    tickets: U32 # t
    pre_images: U32 # p
    pre_images_size: U32 # d
    guarantees: U32 # g
    assurances: U32 # a

    @staticmethod
    def empty() -> "ValidatorStat":
        return ValidatorStat.from_json(
            {
                "blocks": 0,
                "tickets": 0,
                "pre_images": 0,
                "pre_images_size": 0,
                "guarantees": 0,
                "assurances": 0,
            }
        )


@structure
class CoreStat:
    da_load: Uint # d
    popularity: Uint  # p
    imports: Uint  # i
    exports: Uint  # e
    extrinsic_size: Uint  # z
    extrinsic_count: Uint  # x
    bundle_size: Uint  # l
    gas_used: Uint  # u

    @staticmethod
    def empty() -> "CoreStat":
        return CoreStat(
            gas_used=Uint(0),
            imports=Uint(0),
            extrinsic_count=Uint(0),
            extrinsic_size=Uint(0),
            exports=Uint(0),
            bundle_size=Uint(0),
            da_load=Uint(0),
            popularity=Uint(0),
        )


@structure
class ServiceStat:
    provided_count: Uint # p[0]
    provided_size: Uint  # p[1]
    refinement_count: Uint  # r[0]
    refinement_gas_used: Uint  # r[1]
    imports: Uint  # i
    exports: Uint  # e
    extrinsic_size: Uint  # z
    extrinsic_count: Uint  # x
    accumulate_count: Uint  # a[0]
    accumulate_gas_used: Uint  # a[1]
    on_transfers_count: Uint  # t[0]
    on_transfers_gas_used: Uint  # t[1]

    @staticmethod
    def empty() -> "ServiceStat":
        return ServiceStat.from_json(
            {
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
            }
        )


class AllValidatorStats(TypedArray[ValidatorStat, VALIDATOR_COUNT]):
    """All validator stats"""

    @staticmethod
    def empty() -> "AllValidatorStats":
        return AllValidatorStats(
            [ValidatorStat.empty() for _ in range(VALIDATOR_COUNT)]
        )


class AllCoreStats(TypedArray[CoreStat, CORE_COUNT]):
    """All core stats"""

    @staticmethod
    def empty():
        return AllCoreStats([CoreStat.empty() for _ in range(CORE_COUNT)])


class AllServiceStats(Dictionary[ServiceId, ServiceStat, "id", "record"]):
    """All service stats"""
    ...

@structure
class Pi:
    """
    Component: π
    Key: 13

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/192b00192b00?v=0.7.0
    """

    vals_current: AllValidatorStats
    vals_last: AllValidatorStats
    cores: AllCoreStats
    services: AllServiceStats
