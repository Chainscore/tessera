import asyncio
import time
from typing import Callable, List, Tuple

from jam.logging import get_logger
from .handlers import WPBuilder, assurer, BlockProducer, conductor
from .dispatcher import NodeDispatcher
from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH


logger = get_logger("nodeops")


def dispatch_fns(is_bd: bool) -> List[Tuple[int, NodeDispatcher]]:
    if is_bd:
        return [(0, WPBuilder)]

    return [
        (0, BlockProducer),
        (2, None),  # audit
        (4, assurer),  # transmit assurances
    ]


async def schedule_run(sch_ts: int, runner: NodeDispatcher, *args) -> None:
    await asyncio.sleep(sch_ts)
    await runner.run(*args)


async def operate(is_builder):
    """
    Starts a never ending 6-sec loop
    """
    curr_time = time.time()
    ts = int((curr_time - GENESIS_TS) // 6)
    conductor_ts = max((EPOCH_LENGTH // 60), 1)

    while True:
        # If we not yet in ts timeslot, sleep for a while
        ts_start_time = GENESIS_TS + ts * 6
        curr_time = time.time()
        if curr_time < ts_start_time:
            await asyncio.sleep(ts_start_time - curr_time)
        logger.debug("Node operations started for a new timeslot", time_slot=ts)

        if (ts % EPOCH_LENGTH) == conductor_ts:
            asyncio.create_task(conductor.run(time_slot=ts)) # generate and transmit ticket

        # Schedule tasks to run immediately
        for dispatch in dispatch_fns(is_builder):
            (task_ts, runner) = dispatch
            if runner:
                asyncio.create_task(schedule_run(task_ts, runner, ts))

        # Move on to next timeslot and sleep
        ts += 1
