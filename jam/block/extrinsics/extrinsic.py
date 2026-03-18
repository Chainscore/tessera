from typing import TYPE_CHECKING
from tsrkit_types import Bytes, Uint
from jam.block.errors import BlockError, BlockErrorCode
from jam.types.protocol.crypto import Hash
from tsrkit_types.struct import structure
from jam.block.extrinsics.tickets import TicketsExtrinsic
from jam.block.extrinsics.preimages import PreimagesExtrinsic
from jam.block.extrinsics.guarantees import GuaranteesExtrinsic
from jam.block.extrinsics.assurances import AssurancesExtrinsic
from jam.block.extrinsics.disputes import DisputesExtrinsic, Culprits, Faults, Verdicts

if TYPE_CHECKING:
    from jam.block.header.header import Header


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

    def hash(self) -> Bytes[32]:
        gr = Uint(len(self.guarantees)).encode() + b"".join(
            [
                Hash.blake2b(g.report.encode()) + g.slot.encode() + g.signatures.encode()
                for g in self.guarantees
            ]
        )
        return Hash.blake2b(
            bytes(Hash.blake2b(self.tickets.encode()))
            + bytes(Hash.blake2b(self.preimages.encode()))
            + bytes(Hash.blake2b(gr))
            + bytes(Hash.blake2b(self.assurances.encode()))
            + bytes(Hash.blake2b(self.disputes.encode()))
        )

    def validate(self, header: "Header") -> bool:
        # Valid extrinsics hash
        if self.hash() != header.extrinsic_hash:
            raise BlockError(BlockErrorCode.INCORRECT_EXTRINSIC_HASH)
        return True
