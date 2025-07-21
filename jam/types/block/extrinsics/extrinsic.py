from tsrkit_types.struct import structure

from jam.types.block.extrinsics.tickets import TicketsExtrinsic
from jam.types.block.extrinsics.preimages import PreimagesExtrinsic
from jam.types.block.extrinsics.guarantees import GuaranteesExtrinsic
from jam.types.block.extrinsics.assurances import AssurancesExtrinsic
from jam.types.block.extrinsics.disputes import (
    DisputesExtrinsic,
    Culprits,
    Faults,
    Verdicts,
)


@structure
class Extrinsic:
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
            disputes=DisputesExtrinsic(
                verdicts=Verdicts([]), culprits=Culprits([]), faults=Faults([])
            ),
        )
