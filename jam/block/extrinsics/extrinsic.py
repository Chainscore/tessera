from typing import TYPE_CHECKING
from tsrkit_types import Bytes, Uint
from jam.block.errors import BlockError, BlockErrorCode
from jam.types.protocol.crypto import Hash
from jam.utils.constants import CORE_COUNT, MAX_TICKETS_PER_EXTRINSIC, EPOCH_LENGTH, TICKET_SUBMISSION_END
from tsrkit_types.struct import structure
from jam.block.extrinsics.tickets import TicketsExtrinsic, TicketEnvelope
from jam.block.extrinsics.preimages import PreimagesExtrinsic
from jam.block.extrinsics.guarantees import GuaranteesExtrinsic
from jam.block.extrinsics.assurances import AssurancesExtrinsic
from jam.block.extrinsics.disputes import DisputesExtrinsic, Culprits, Faults, Verdicts
from jam.types.protocol.crypto import (
    BandersnatchRingVrfSignature,
    Hash,
    OpaqueHash,
)
from py_ark_vrf import vrf_output

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

    @staticmethod
    def get_vrf_output(signature: BandersnatchRingVrfSignature) -> OpaqueHash:
        # return Bytes[32](RingVrf.pedersen_proof_to_hash(signature))
        return OpaqueHash(vrf_output(signature)[:32])

    @classmethod
    def from_collected(cls, time_slot):
        # --- Extrinsic Collection --- #
        eg, et, ea, ep, ed = GuaranteesExtrinsic([]), [], [], PreimagesExtrinsic([]), DisputesExtrinsic.empty()
        from .tickets import ticket_store
        from .guarantees import wrg_store
        from .assurances import asr_store
        from .preimages import preimg_store
        from .disputes import dpt_store

        # Sort Assurances
        ea = AssurancesExtrinsic(sorted(asr_store._store, key=lambda a: a.validator_index))

        # Filter Guarantees
        rg_cores = set()
        for rg in wrg_store._store:
            if rg.report.core_index not in rg_cores:
                eg.append(rg)
                rg_cores.add(rg.report.core_index)

            if len(eg) >= CORE_COUNT:
                break
        rg_cores.clear()

        ep = PreimagesExtrinsic(preimg_store._store[:])


        # Already sorted
        ed = DisputesExtrinsic(dpt_store._store)


        def sort_fn(ticket: TicketEnvelope) -> int:
            # Take VRF output of the signature and sort by it
            return int.from_bytes(Extrinsic.get_vrf_output(ticket.signature))

        if time_slot%EPOCH_LENGTH < TICKET_SUBMISSION_END:
            print(f"Including tickets in block, time_slot={time_slot}, slot={time_slot%EPOCH_LENGTH}")
            et = TicketsExtrinsic(ticket_store._store[:MAX_TICKETS_PER_EXTRINSIC])
            et.sort(key=sort_fn)
            print("Number of tickets included", len(et))

        else:
            print(f"Tickets are not allowed in block after TICKET_SUBMISSION_END, time_slot={time_slot}, slot={time_slot%EPOCH_LENGTH}")
            et = TicketsExtrinsic([])

        return Extrinsic(
            tickets=et,
            preimages=ep,
            guarantees=eg,
            assurances=ea,
            disputes=ed,
        )

    def clear_from_stores(self):
        """
        Assumes that the current extrinsics were imported and need not be stored in our
        extrinsic stores, so here we'll remove them
        """
        from .tickets import ticket_store
        from .guarantees import wrg_store
        from .assurances import asr_store
        from .disputes import dpt_store

        ticket_store.remove(self.tickets)
        wrg_store.remove(self.guarantees)
        asr_store.remove(self.assurances)
        dpt_store.remove(self.disputes)
        return

    def validate(self, header: "Header") -> bool:
        # Valid extrinsics hash
        if self.hash() != header.extrinsic_hash:
            raise BlockError(BlockErrorCode.INCORRECT_EXTRINSIC_HASH)
        return True
