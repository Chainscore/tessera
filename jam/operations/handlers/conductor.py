import asyncio
from tsrkit_types import U32
from jam.types.protocol.ticket import TicketAttempt
from jam.block.extrinsics.tickets import TicketEnvelope
from jam.types.protocol.crypto import BandersnatchRingVrfSignature
from jam.types.protocol.core import TimeSlot
from dot_ring.vrf.ring.ring_vrf import RingVrf
from jam.logging import get_logger
from jam.utils.constants import EPOCH_LENGTH, X, TICKET_ENTRIES_PER_VALIDATOR
from jam.network.protocols.ce_131 import SafroleTicketProxyDistribution, CE131Data, EpochTicket

logger = get_logger("nodeops")

class Conductor:
    
    @classmethod 
    async def run(cls, time_slot: TimeSlot):
        from jam.network.node import node
        from jam.state.state import state
        CE131 = SafroleTicketProxyDistribution()

        if int(node.port) != 40000:
            print("Not generating ticket")
            return

        try:
            tasks = []
            # generating & transmitting all the tickets allowed per validator
            for i in range(TICKET_ENTRIES_PER_VALIDATOR):
                epoch_index = U32(time_slot // EPOCH_LENGTH)
                ticket_envelope = cls.generate_ticket(state, i)

                if ticket_envelope is not None:
                    epoch_ticket = EpochTicket(epoch_index=epoch_index, ticket=ticket_envelope)
                    epoch_ticket_len = U32(len(epoch_ticket.encode()))

                    data = CE131Data(epoch_ticket_len=epoch_ticket_len, epoch_ticket=epoch_ticket)

                    task = CE131.transmit(node, data)
                    tasks.append(task)
                else:
                    raise ValueError("Ticket generation failed")

            ack = await asyncio.gather(*tasks)
            logger.info(
                "Ticket transmission completed",
                node_name=node.name,
                total_guarantors=len(node.peer_conn),
            )

        except Exception as e:
            logger.error("Failed to generate & transmit safrol ticket", error=e, time_slot=time_slot)
    
    @classmethod
    def generate_ticket(cls, state, attempt: int) -> TicketEnvelope | None:
        from jam.settings import settings

        eta = state.eta[2]
        vals = [k.bandersnatch for k in state.gamma.k]

        try:
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
        except Exception as e:
            logger.error("Failed to generate ticket", error=e)

conductor = Conductor()