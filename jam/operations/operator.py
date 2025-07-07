import asyncio
import time
from typing import Callable, List, Tuple
from .assr_collector import assr_collector
from .bp_engine import BlockProducer
from .dispatcher import NodeDispatcher
from jam.utils.constants import GENESIS_TS 


dispatch_fns: List[Tuple[int, NodeDispatcher]] = [
    (0, BlockProducer),
    # (0, Builder),
    (2, None), # audit
    (4, assr_collector), # transmit assurances
]


async def schedule_run(sch_ts: int, runner: NodeDispatcher, *args) -> None:
    await asyncio.sleep(sch_ts)
    await runner.run(*args)


async def operate():
    """
    Starts a never ending 6-sec loop
    """
    curr_time = time.time()
    ts = int((curr_time - GENESIS_TS) // 6) 
    
    while True:
        # If we not yet in ts timeslot, sleep for a while
        ts_start_time = GENESIS_TS + ts * 6
        curr_time = time.time()
        if curr_time < ts_start_time:
            await asyncio.sleep(ts_start_time - curr_time)
        print("Started TS", ts, int(time.time())) 
        # Schedule tasks to run immediately
        for dispatch in dispatch_fns:
            (task_ts, runner) = dispatch
            if runner: asyncio.create_task(schedule_run(task_ts, runner, ts))

        # Move on to next timeslot and sleep
        ts += 1
