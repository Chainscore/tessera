from typing import TYPE_CHECKING
from jam.block.errors import BlockError, BlockErrorCode
from jam.types.protocol.crypto import Hash
from jam.utils.constants import CORE_COUNT, MAX_TICKETS_PER_EXTRINSIC
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

    @classmethod
    def from_collected(cls):
        # --- Extrinsic Collection --- #
        eg, et, ea, ep = GuaranteesExtrinsic([]), [], [], PreimagesExtrinsic([])
        from .tickets import ticket_store
        from .guarantees import wrg_store
        from .assurances import asr_store
        from .preimages import preimg_store

        for rg in wrg_store._store:
            # TODO: Filtering - Take only one WR per core [?]
            eg.append(rg)
            if len(eg) >= CORE_COUNT:
                break
        ep = PreimagesExtrinsic(preimg_store._store[:])
        et = TicketsExtrinsic(ticket_store._store[:MAX_TICKETS_PER_EXTRINSIC])
        ea = AssurancesExtrinsic(asr_store._store)
        return Extrinsic(tickets=et, preimages=ep, guarantees=eg, assurances=ea, disputes=DisputesExtrinsic.empty())

    def clear_from_stores(self):
        """
        Assumes that the current extrinsics were imported and need not be stored in our
        extrinsic stores, so here we'll remove them
        """
        from .tickets import ticket_store
        from .guarantees import wrg_store
        from .assurances import asr_store

        ticket_store.remove(self.tickets)
        wrg_store.remove(self.guarantees)
        asr_store.remove(self.assurances)
        # TODO: Handle disputes
        return

    def validate(self, header: "Header"):
        # Valid extrinsics hash 
        if Hash.blake2b(self.encode()) != header.extrinsic_hash:
            raise BlockError(BlockErrorCode.INCORRECT_EXTRINSIC_HASH)
        return
