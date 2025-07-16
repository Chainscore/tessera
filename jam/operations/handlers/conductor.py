from jam.types.protocol.ticket import TicketAttempt
from jam.block.extrinsics.tickets import TicketEnvelope
from jam.types.protocol.crypto import BandersnatchRingVrfSignature
from jam.types.protocol.core import TimeSlot
from dot_ring.vrf.ring.ring_vrf import RingVrf

from jam.utils.constants import EPOCH_LENGTH, X


class Conductor:

    @classmethod
    def run(cls, time_slot: TimeSlot): ...

    @classmethod
    def generate_ticket(cls, state, attempt: int) -> TicketEnvelope:
        from jam.settings import settings

        eta = state.eta[2]
        vals = [k.bandersnatch for k in state.gamma.k]

        return TicketEnvelope(
            attempt=TicketAttempt(attempt),
            signature=BandersnatchRingVrfSignature(
                RingVrf.ring_vrf_proof(
                    X.TICKET.value + eta + bytes([attempt]),
                    b"",
                    settings.bandersnatch_private,
                    settings.bandersnatch_public,
                    vals,
                    False,
                )
            ),
        )
