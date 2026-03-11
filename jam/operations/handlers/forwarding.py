from asyncio import sleep
from collections import deque
from time import time
from math import ceil
from typing import TYPE_CHECKING

from jam.operations.dispatcher import NodeDispatcher
from jam.utils.task_utils import create_safe_task
from jam.types.protocol.core import TimeSlot
from tsrkit_types import U32
from jam.utils.constants import TICKET_SUBMISSION_END, GENESIS_TS
from jam.network.protocols.ce_132 import CE132Data

if TYPE_CHECKING:
    from jam.jam_node import JamNode


class Forwarding(NodeDispatcher):

    def __init__(self, jam: "JamNode") -> None:
        super().__init__(jam)
        self._queue: deque = deque()

    def enqueue(self, item):
        self._queue.append(item)

    def dequeue(self):
        if self.is_empty():
            return None
        return self._queue.popleft()

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def pending(self) -> int:
        return len(self._queue)

    async def run(self, slot: U32, time_slot: TimeSlot):
        try:
            if self.is_empty():
                return

            ts = time_slot
            ticket_submission_end = TICKET_SUBMISSION_END // 2

            if ticket_submission_end != slot:
                slots_available = ticket_submission_end - slot
                tickets_per_slot = ceil(self.pending() / slots_available)

                for i in range(tickets_per_slot):
                    ticket = self.dequeue()
                    if ticket:
                        data = CE132Data(epoch_ticket_len=ticket.epoch_ticket_len, epoch_ticket=ticket.epoch_ticket)
                        create_safe_task(
                            self.router.dispatch(132, data),
                            name="Transmit Ticket Forward",
                        )
                        ts += 1
                        curr_time = time()
                        next_time_slot_time = ts * 6 + GENESIS_TS
                        if curr_time < next_time_slot_time:
                            await sleep(next_time_slot_time - curr_time)

        except Exception as e:
            self.logger.error("Failed to forward ticket", error=e, time_slot=time_slot)
