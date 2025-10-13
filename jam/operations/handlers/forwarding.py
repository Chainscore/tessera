from asyncio import sleep
from time import time
from math import ceil
from jam.types.protocol.core import TimeSlot
from tsrkit_types import U32
from jam.log_setup import node_logger as logger
from jam.utils.constants import TICKET_SUBMISSION_END, GENESIS_TS
from jam.network.protocols.ce_132 import SafroleTicketDistribution, CE132Data


class Forwarding:

    @classmethod
    async def run(cls, slot: U32, time_slot: TimeSlot):
        try:
            from jam.operations.ticket_queue import ticket_queue
            if not ticket_queue.is_empty():
                ts = time_slot
                ticket_submission_end = TICKET_SUBMISSION_END // 2

                if ticket_submission_end != slot:
                    slots_available = ticket_submission_end - slot
                    tickets_per_slot = ceil(ticket_queue.length() / slots_available)

                    for i in range(tickets_per_slot):
                        ticket = ticket_queue.pop()
                        if ticket:
                            CE132 = SafroleTicketDistribution()
                            data = CE132Data(epoch_ticket_len=ticket.epoch_ticket_len, epoch_ticket=ticket.epoch_ticket)
                            responses = await CE132.transmit(data)
                            ts += 1
                            curr_time = time()
                            next_time_slot_time = ts * 6 + GENESIS_TS
                            if curr_time < next_time_slot_time:
                                await sleep(next_time_slot_time - curr_time)

        except Exception as e:
            logger.error("Failed to forward ticket", error=e, time_slot=time_slot)


