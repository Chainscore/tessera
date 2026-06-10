import asyncio
from jam.operations.dispatcher import NodeDispatcher
from tsrkit_types import U32
from jam.models.protocol.ticket import TicketAttempt
from jam.block.extrinsics.tickets import TicketEnvelope
from jam.models.protocol.crypto import BandersnatchRingVrfSignature
from jam.models.protocol.core import TimeSlot
from dot_ring import Bandersnatch, RingVRF
from jam.log_setup import node_logger as logger
from jam.utils.constants import EPOCH_LENGTH, X, ticket_entries_for_validator_count
from jam.network.protocols.ce_131 import SafroleTicketProxyDistribution, CE131Data, EpochTicket


class Conductor(NodeDispatcher):

    # TODO: pass node as parameter
    @classmethod 
    async def run(cls, time_slot: TimeSlot, finality_time_slot: TimeSlot, state=None):
        try:
            from jam.network.start import node
            CE131 = SafroleTicketProxyDistribution()
            tasks = []
            # generating & transmitting all the tickets allowed per validator
            if not state:
                from jam.state.state import state
            for i in range(ticket_entries_for_validator_count(len(state.gamma.p))):
                ticket_envelope = cls.generate_ticket(state, i)
                epoch_index = U32(finality_time_slot // EPOCH_LENGTH)

                if ticket_envelope is not None:
                    epoch_ticket = EpochTicket(epoch_index=epoch_index, ticket=ticket_envelope)
                    epoch_ticket_len = U32(len(epoch_ticket.encode()))

                    data = CE131Data(epoch_ticket_len=epoch_ticket_len, epoch_ticket=epoch_ticket)

                    task = CE131.transmit(data, state)
                    tasks.append(task)
                else:
                    raise ValueError("Ticket generation failed")

            ack = await asyncio.gather(*tasks)

        except Exception as e:
            logger.error("Failed to generate & transmit ticket", error=e, time_slot=time_slot)
    
    @classmethod
    def generate_ticket(cls, state, attempt: int) -> TicketEnvelope | None:
        from jam.settings import settings

        eta = state.eta[2]
        vals = [bytes(k.bandersnatch) for k in state.gamma.p]

        try:
            from jam.state.transitions.safrole.safrole import Safrole

            ring  =Safrole.build_ring(vals)
            ring_root = Safrole.build_ring_root(ring)
            # Use dot_ring for proof generation (consistent with validation)
            ring_proof = RingVRF[Bandersnatch].prove(
                alpha=X.TICKET.value + eta + bytes([attempt]),
                ad=b"",
                secret_key=settings.bandersnatch_private,
                producer_key=settings.bandersnatch_public,
                ring=ring,
                ring_root=ring_root,
            )
            return TicketEnvelope(
                attempt=TicketAttempt(attempt),
                signature=BandersnatchRingVrfSignature(ring_proof.to_bytes()),
            )
        except Exception as e:
            logger.error("Failed to generate ticket", error=e)
