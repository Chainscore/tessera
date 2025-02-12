from dataclasses import dataclass
from jam.types.header import Header
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
    extrinsic: Extrinsic
