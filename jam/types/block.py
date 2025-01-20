from dataclasses import dataclass
from jam.types.header import Header
from jam.utils.codec.codable import Codable
from jam.types.extrinsics import (
    TicketsExtrinsic, PreimagesExtrinsic,
    GuaranteesExtrinsic, AssurancesExtrinsic,
    DisputesExtrinsic
)
from jam.utils.codec.composite.dataclasses import decodable_dataclass

@decodable_dataclass
@dataclass
class Extrinsic(Codable):
    """Extrinsic structure."""
    tickets: TicketsExtrinsic
    preimages: PreimagesExtrinsic
    guarantees: GuaranteesExtrinsic
    assurances: AssurancesExtrinsic
    disputes: DisputesExtrinsic

@decodable_dataclass
@dataclass
class Block(Codable):
    """Block structure."""
    header: Header
    extrinsic: Extrinsic
