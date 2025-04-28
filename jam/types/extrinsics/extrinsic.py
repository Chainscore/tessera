from dataclasses import dataclass
from jam.types.extrinsics import (
    TicketsExtrinsic,
    PreimagesExtrinsic,
    GuaranteesExtrinsic,
    AssurancesExtrinsic,
    DisputesExtrinsic,
)
from jam.types.extrinsics.disputes import Culprits, Faults, Verdicts
from jam.utils.codec.codable import Codable
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

    @staticmethod
    def empty() -> "Extrinsic":
        return Extrinsic(
            tickets=TicketsExtrinsic([]),
            preimages=PreimagesExtrinsic([]),
            guarantees=GuaranteesExtrinsic([]),
            assurances=AssurancesExtrinsic([]),
            disputes=DisputesExtrinsic(verdicts=Verdicts([]), culprits=Culprits([]), faults=Faults([]))
        )