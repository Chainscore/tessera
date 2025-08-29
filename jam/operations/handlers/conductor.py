import asyncio
from tsrkit_types import U32
from jam.types.protocol.ticket import TicketAttempt
from jam.block.extrinsics.tickets import TicketEnvelope
from jam.types.protocol.crypto import BandersnatchRingVrfSignature
from jam.types.protocol.core import TimeSlot
from py_ark_vrf import prove_ring
from jam.logging import get_logger
from jam.utils.constants import EPOCH_LENGTH, X, TICKET_ENTRIES_PER_VALIDATOR
from jam.network.protocols.ce_131 import SafroleTicketProxyDistribution, CE131Data, EpochTicket

logger = get_logger("nodeops")

class Conductor:
    
    @classmethod 
    async def run(cls, time_slot: TimeSlot, finality_time_slot: TimeSlot):
        try:
            from jam.network.start import node
            CE131 = SafroleTicketProxyDistribution()
            tasks = []
            # generating & transmitting all the tickets allowed per validator
            for i in range(TICKET_ENTRIES_PER_VALIDATOR):
                from jam.state.state import state
                ticket_envelope = cls.generate_ticket(state, i)
                epoch_index = U32(finality_time_slot // EPOCH_LENGTH)

                if ticket_envelope is not None:
                    epoch_ticket = EpochTicket(epoch_index=epoch_index, ticket=ticket_envelope)
                    epoch_ticket_len = U32(len(epoch_ticket.encode()))

                    data = CE131Data(epoch_ticket_len=epoch_ticket_len, epoch_ticket=epoch_ticket)

                    task = CE131.transmit(data)
                    tasks.append(task)
                else:
                    raise ValueError("Ticket generation failed")

            ack = await asyncio.gather(*tasks)
            logger.info("Ticket transmission completed", port=node.port)

        except Exception as e:
            logger.error("Failed to generate & transmit safrole ticket", error=e, time_slot=time_slot)
    
    @classmethod
    def generate_ticket(cls, state, attempt: int) -> TicketEnvelope | None:
        from jam.settings import settings

        eta = state.eta[2]
        vals = [k.bandersnatch for k in state.gamma.p]

        try:
            return TicketEnvelope(
                attempt=TicketAttempt(attempt),
                signature=BandersnatchRingVrfSignature(
                    prove_ring(
                        secret_scalar=settings.bandersnatch_private,
                        input_data=X.TICKET.value + eta + bytes([attempt]),
                        ring=vals,
                        aux=b"",
                    )
                ),
            )
        except Exception as e:
            logger.error("Failed to generate ticket", error=e)
