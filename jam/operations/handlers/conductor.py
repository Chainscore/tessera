from jam.operations.dispatcher import NodeDispatcher
from tsrkit_types import U32
from jam.types.protocol.ticket import TicketAttempt
from jam.block.extrinsics.tickets import TicketEnvelope
from jam.types.protocol.crypto import BandersnatchRingVrfSignature
from jam.types.protocol.core import TimeSlot
from dot_ring import RingVRF, Bandersnatch
from jam.utils.constants import EPOCH_LENGTH, X, TICKET_ENTRIES_PER_VALIDATOR
from jam.utils.gather import gather_with_exceptions
from jam.network.protocols.ce_131 import CE131Data, EpochTicket


class Conductor(NodeDispatcher):

    async def run(self, time_slot: TimeSlot, finality_time_slot: TimeSlot):
        try:
            state = self.state
            tasks = []

            for i in range(TICKET_ENTRIES_PER_VALIDATOR):
                ticket_envelope = self.generate_ticket(state, i)
                epoch_index = U32(finality_time_slot // EPOCH_LENGTH)

                if ticket_envelope is not None:
                    epoch_ticket = EpochTicket(epoch_index=epoch_index, ticket=ticket_envelope)
                    epoch_ticket_len = U32(len(epoch_ticket.encode()))
                    data = CE131Data(epoch_ticket_len=epoch_ticket_len, epoch_ticket=epoch_ticket)

                    tasks.append(self.router.dispatch(131, data))
                else:
                    raise ValueError("Ticket generation failed")

            await gather_with_exceptions(tasks, name="Transmit Tickets")

        except Exception as e:
            self.logger.error("Failed to generate & transmit ticket", error=e, time_slot=time_slot)

    def generate_ticket(self, state, attempt: int) -> TicketEnvelope | None:
        settings = self.settings

        eta = state.eta[2]
        vals = [bytes(k.bandersnatch) for k in state.gamma.p]

        try:
            ring_proof = RingVRF[Bandersnatch].prove(
                alpha=X.TICKET.value + eta + bytes([attempt]),
                ad=b"",
                secret_key=settings.bandersnatch_private,
                producer_key=settings.bandersnatch_public,
                keys=vals,
            )
            return TicketEnvelope(
                attempt=TicketAttempt(attempt),
                signature=BandersnatchRingVrfSignature(ring_proof.to_bytes()),
            )
        except Exception as e:
            self.logger.error("Failed to generate ticket", error=e)
