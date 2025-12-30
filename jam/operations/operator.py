import asyncio
import math
import time
from typing import List, Tuple

from jam.log_setup import node_logger as logger
from .handlers import WPBuilder, assurer, BlockProducer, Conductor, Forwarding
from .dispatcher import NodeDispatcher
from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, TICKET_SUBMISSION_END
from ..finality.finality import Finality


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

        from jam.network.start import node
        if not node:
            ts += 1
            continue
        logger.info(f"New Time Slot #{ts}", slot_index=(ts % EPOCH_LENGTH), epoch=int(ts // EPOCH_LENGTH), peers=len(node.active_peers), connections=len(node.all_connected))
        # Schedule tasks to run immediately

        from jam.settings import settings
        main_db = settings.main_db
        finality_block = Finality.load_final(main_db)
        finality_time_slot = finality_block.header.slot

        if conductor_ts <= (finality_time_slot%EPOCH_LENGTH) < (TICKET_SUBMISSION_END // 2) and not ticket_generated:
            asyncio.create_task(schedule_run(0, Conductor, ts, finality_time_slot))
            ticket_generated = True

        if forwarding_s <= (finality_time_slot%EPOCH_LENGTH) < (TICKET_SUBMISSION_END // 2):
            asyncio.create_task(schedule_run(0, Forwarding, finality_time_slot%EPOCH_LENGTH, finality_time_slot))

        for dispatch in dispatch_fns(is_builder):
            (task_ts, runner) = dispatch
            if runner:
                asyncio.create_task(schedule_run(task_ts, runner, ts))

        if ts%EPOCH_LENGTH == 11:
            ticket_generated = False
            from jam.block.extrinsics.tickets import ticket_store
            from jam.block.extrinsics.guarantees import wrg_store
            from jam.block.extrinsics.assurances import asr_store
            from jam.block.extrinsics.disputes import dpt_store
            ticket_store.clear()
            # wrg_store.clear()
            # asr_store.clear()
            dpt_store.clear()

        if ts%EPOCH_LENGTH == 0:
            from jam.settings import settings
            settings.update()

        # Move on to next timeslot and sleep
        ts += 1
