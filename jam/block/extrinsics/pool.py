from jam.block.extrinsics.store import ExtrinsicStore
from jam.block.extrinsics.preimage_store import PreimageStore

from jam.block.extrinsics.tickets import TicketEnvelope, TicketsExtrinsic
from jam.block.extrinsics.guarantees import ReportGuarantee, GuaranteesExtrinsic
from jam.block.extrinsics.assurances import AvailAssurance, AssurancesExtrinsic
from jam.block.extrinsics.preimages import PreimagesExtrinsic
from jam.block.extrinsics.disputes import DisputesExtrinsic, Culprits, Faults, Verdicts
from jam.block.extrinsics.extrinsic import Extrinsic

from dot_ring import RingVRF, Bandersnatch

from jam.utils.constants import CORE_COUNT, MAX_TICKETS_PER_EXTRINSIC, EPOCH_LENGTH, TICKET_SUBMISSION_END


class ExtrinsicPool:
    """
    Holds all extrinsic stores for the node.
    Responsible for building block extrinsics from collected data
    and clearing stores after block import.
    """

    def __init__(self):
        self.tickets = ExtrinsicStore[TicketEnvelope]()
        self.guarantees = ExtrinsicStore[ReportGuarantee]()
        self.assurances = ExtrinsicStore[AvailAssurance]()
        self.preimages = PreimageStore()
        self.disputes = ExtrinsicStore[DisputesExtrinsic]()

    def build_extrinsics(self, time_slot: int) -> Extrinsic:
        """Build block extrinsics from all collected stores."""

        # Assurances: sorted by validator index
        ea = AssurancesExtrinsic(sorted(self.assurances._store, key=lambda a: a.validator_index))

        # Guarantees: deduplicated by core index
        eg = GuaranteesExtrinsic([])
        rg_cores = set()
        for rg in self.guarantees._store:
            if rg.report.core_index not in rg_cores:
                eg.append(rg)
                rg_cores.add(rg.report.core_index)
            if len(eg) >= CORE_COUNT:
                break

        # Preimages: sorted by (requester, blob)
        ep = PreimagesExtrinsic(list(self.preimages._store.values()))
        ep.sort(key=lambda p: (int(p.requester), p.blob))

        # Disputes
        if self.disputes._store:
            ed = DisputesExtrinsic(
                verdicts=Verdicts([d.verdicts for d in self.disputes._store]),
                culprits=Culprits([d.culprits for d in self.disputes._store]),
                faults=Faults([d.faults for d in self.disputes._store]),
            )
        else:
            ed = DisputesExtrinsic.empty()

        # Tickets: sorted by VRF output, only within submission window
        if time_slot % EPOCH_LENGTH < TICKET_SUBMISSION_END:
            et = TicketsExtrinsic(self.tickets._store[:MAX_TICKETS_PER_EXTRINSIC])
            et.sort(key=self._ticket_sort_key)
        else:
            et = TicketsExtrinsic([])

        return Extrinsic(
            tickets=et,
            preimages=ep,
            guarantees=eg,
            assurances=ea,
            disputes=ed,
        )

    def clear(self, extrinsic: Extrinsic):
        """Remove extrinsics that were included in a block."""
        self.tickets.remove(extrinsic.tickets)
        self.guarantees.remove(extrinsic.guarantees)
        self.assurances.remove(extrinsic.assurances)
        self.preimages.remove(extrinsic.preimages)
        self.disputes.remove(extrinsic.disputes)

    @staticmethod
    def _ticket_sort_key(ticket: TicketEnvelope) -> int:
        ring_proof = RingVRF[Bandersnatch].from_bytes(ticket.signature, skip_pedersen=False)
        return int.from_bytes(ring_proof.proof_to_hash(ring_proof.pedersen_proof.output_point)[:32])
