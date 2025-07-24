import asyncio
import time
from typing import List, Tuple

from jam.logging import get_logger
from .handlers import conductor
from .dispatcher import NodeDispatcher
from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, TICKET_SUBMISSION_END
from jam.network.protocols.ce_132 import forwarding


logger = get_logger("nodeops")


def dispatch_fns(is_bd: bool, is_generating: bool) -> List[Tuple[int, NodeDispatcher]] | None:
    if not is_bd:
        if is_generating:
            return [
                (0, conductor),
            ]


async def schedule_run(sch_ts: int, runner: NodeDispatcher, *args) -> None:
    await asyncio.sleep(sch_ts)
    await runner.run(*args)


async def epoch_operate(is_builder = False):
    """
    Starts a never ending 3600 sec loop
    """
    curr_time = time.time()
    ts = int((curr_time - GENESIS_TS) // 6)
    conductor_s = max((EPOCH_LENGTH // 60), 1)
    forwarding_s = max((EPOCH_LENGTH // 20), 1)
    ticket_generated = False

    print("conductor_s", conductor_s)
    print("forwarding_s", forwarding_s)
    print("starting slot", ts%EPOCH_LENGTH)
    print("safrol ending", TICKET_SUBMISSION_END // 2)

    while True:
        from jam.network.start import node
        if node:
            # print("Current timeslot", ts)
            slot = ts%EPOCH_LENGTH
            # logger.debug("Slot", slot=slot)

            if slot < conductor_s:
                logger.debug(f"Sleeping till {conductor_s}")
                sleep_time = (conductor_s - slot)*6
                await asyncio.sleep(sleep_time)
                ts += (conductor_s - slot)

            elif (conductor_s <= slot < (TICKET_SUBMISSION_END // 2)) and not ticket_generated:
                print("Generating tickets")
                for dispatch in dispatch_fns(is_builder, is_generating=True):
                    (task_ts, runner) = dispatch
                    if runner:
                        asyncio.create_task(schedule_run(task_ts, runner, ts))
                    ticket_generated=True
                ts += 1
                curr_time = time.time()
                next_time_slot_time = ts*6 + GENESIS_TS
                if curr_time < next_time_slot_time:
                    await asyncio.sleep(next_time_slot_time - curr_time)
                ts += 1

            elif forwarding_s <= slot < (TICKET_SUBMISSION_END // 2):
                print("Starting ticket forwarding")
                from jam.operations.ticket_queue import ticket_queue
                print("Ticket queue length", ticket_queue.length(), ticket_queue.is_empty())
                asyncio.create_task(forwarding(slot, ts))
                ts += 1
                curr_time = time.time()
                next_time_slot_time = ts * 6 + GENESIS_TS
                if curr_time < next_time_slot_time:
                    await asyncio.sleep(next_time_slot_time - curr_time)
                ts += 1
            else:
                ts += 1
                slot = ts % EPOCH_LENGTH
                logger.debug("Sleeping for remaining epoch")
                sleep_time = (EPOCH_LENGTH - slot)*6
                await asyncio.sleep(sleep_time)
                ts += (EPOCH_LENGTH - slot)
        else:
            logger.debug("Node not initialized sleeping for 6 seconds")
            await asyncio.sleep(6)
            ts += 1