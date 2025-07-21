from tsrkit_types import TypedVector
from tsrkit_types.dictionary import Dictionary
from jam.audit import tranche
from jam.audit.tranche_engine import TrancheEngine
from jam.audit.vectors.q import sample_work_reports_with_nulls
from jam.logging import get_logger
from jam.operations.dispatcher import NodeDispatcher
import asyncio
from tsrkit_types.bits import Uint
from jam.network.node import node
from jam.types.work.report import WorkReport
from jam.utils.constants import SLOT_PERIOD, GENESIS_TS
from jam.audit.tranche import JudgmentRecord, Tranche, TrancheState, TrancheStore



# Logger for Block Production / Authoring module
logger = get_logger("author")

class AuditEngine(NodeDispatcher):
    """
    Audit (tranche) engine: after each block (each timeslot), kick off
    the tranche-by-tranche auditing process.
    """

    @classmethod
    async def run(cls, time_slot: int):
        # Ensure network is up
        if not node.is_initialized:
            logger.debug("Network not initialized – skipping audit")
            return
        unaudited_list = sample_work_reports_with_nulls( "jam/combine.json",total_items=10, null_count=3)
        valid_set = TypedVector[WorkReport]([])
        invalid_set = TypedVector[WorkReport]([])
        judgments = Dictionary[WorkReport, JudgmentRecord]({})
        initTranche=Tranche(slot_index=time_slot,tranche_index=0)
        tranche_state=TrancheState(
            unaudited_list=unaudited_list,
            judgments=judgments,
            valid_set=valid_set,
            invalid_set=invalid_set)

        # Build a store for this slot's audit tranches
        store = TrancheStore()
        store.save(initTranche,tranche_state)

        # Instantiate the core tranche engine
        engine = TrancheEngine(store)

        # Drive through all tranches; sleeps internally by AUDIT_PERIOD
        await engine.run(Uint(time_slot))

        # Completed auditing for this slot
        logger.info(f"Finished auditing slot {time_slot}")


# async def heartbeat_loop():
#     """
#     Heartbeat loop: every SLOT_PERIOD seconds, schedule block production,
#     audit engine, and any other timed tasks.
#     """
#     # Align to the next slot boundary
#     now = time.time()
#     next_slot = int((now - GENESIS_TS) // SLOT_PERIOD) + 1
#     while True:
#         ts = next_slot
#         # Schedule block production at t+0s
#         asyncio.create_task(BlockProducer.run(ts))
#         # Schedule audit at t+2s
#         asyncio.create_task(AuditEngine.run(ts))
#         # Sleep until the next slot boundary
#         sleep_until = GENESIS_TS + ts * SLOT_PERIOD - time.time()
#         if sleep_until > 0:
#             await asyncio.sleep(sleep_until)
#         next_slot += 1

# To start heartbeats when node initializes:
# asyncio.create_task(heartbeat_loop())
