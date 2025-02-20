from dataclasses import dataclass

from jam.types import OpaqueHash
from jam.types.header import Header
from jam.types.work.refine_context import OpaqueHashes
from jam.utils.codec.codable import Codable
from jam.types.extrinsics import (
    TicketsExtrinsic,
    PreimagesExtrinsic,
    GuaranteesExtrinsic,
    AssurancesExtrinsic,
    DisputesExtrinsic,
)
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.serde import JsonSerde


@decodable_dataclass
@dataclass
class Extrinsic(Codable, JsonSerde):
    """Extrinsic structure."""

    tickets: TicketsExtrinsic
    preimages: PreimagesExtrinsic
    guarantees: GuaranteesExtrinsic
    assurances: AssurancesExtrinsic
    disputes: DisputesExtrinsic


@decodable_dataclass
@dataclass
class Block(Codable, JsonSerde):
    """Block structure."""

    header: Header
    accumulation_root:OpaqueHash
    extrinsic: Extrinsic
