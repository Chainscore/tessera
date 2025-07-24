import asyncio
import math
import time
from typing import Callable, List, Tuple

from jam.logging import get_logger
from .handlers import WPBuilder, assurer, BlockProducer, conductor
from .dispatcher import NodeDispatcher
from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, TICKET_SUBMISSION_END
from .handlers.conductor import Conductor
from jam.network.protocols.ce_132 import forwarding

logger = get_logger("nodeops")


def dispatch_fns(is_bd: bool, is_generating: bool = False) -> List[Tuple[int, NodeDispatcher]]:
    if is_bd:
        return [(0, WPBuilder)]

    if is_generating:
        return [(0, Conductor)]

    return [
        (0, BlockProducer),
        # (2, None),  # audit
        # (4, assurer),  # transmit assurances
    ]


async def schedule_run(sch_ts: int, runner: NodeDispatcher, *args) -> None:
    await asyncio.sleep(sch_ts)
    await runner.run(*args)

async def schedule_run_2(slot, time_slot) -> None:
    await forwarding(slot, time_slot)


async def operate(is_builder = False):
    """
    Starts a never ending 6-sec loop
    """
    curr_time = time.time()
    ts = math.ceil((curr_time - GENESIS_TS) / 6)
    conductor_ts = max((EPOCH_LENGTH // 60), 1)
    forwarding_s = max((EPOCH_LENGTH // 20), 1)
    ticket_generated = False

    while True:
        # If we not yet in ts timeslot, sleep for a while
        ts_start_time = GENESIS_TS + ts * 6
        curr_time = time.time()
        if curr_time < ts_start_time:
            await asyncio.sleep(ts_start_time - curr_time)

        from jam.state.state import state
        from jam.network.start import node
        if not node:
            ts += 1
            continue
        logger.info(f"New Time Slot #{ts}", slot_index=(ts % EPOCH_LENGTH), peers=len(node.active_peers), connections=len(node.all_connected))
        # Schedule tasks to run immediately

        if conductor_ts < (ts%EPOCH_LENGTH) < (TICKET_SUBMISSION_END // 2) and not ticket_generated:
            for dispatch in dispatch_fns(is_builder ,is_generating=True):
                (task_ts, runner) = dispatch
                if runner:
                    asyncio.create_task(schedule_run(task_ts, runner, ts))
                ticket_generated = True

        if forwarding_s < (ts%EPOCH_LENGTH) < (TICKET_SUBMISSION_END // 2):
            asyncio.create_task(schedule_run_2(ts%EPOCH_LENGTH, ts))

        for dispatch in dispatch_fns(is_builder):
            (task_ts, runner) = dispatch
            if runner:
                asyncio.create_task(schedule_run(task_ts, runner, ts))


        # Move on to next timeslot and sleep
        ts += 1
