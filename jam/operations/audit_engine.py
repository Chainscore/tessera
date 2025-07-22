from tsrkit_types import TypedVector
from tsrkit_types.dictionary import Dictionary

from jam.audit.tranche_engine import TrancheEngine
from jam.audit.q import sample_work_reports_with_nulls
from jam.logging import get_logger
from jam.operations.dispatcher import NodeDispatcher
import asyncio
from tsrkit_types.bits import Uint
from jam.network.node import node
from jam.types.protocol.core import TrancheIndex
from jam.types.protocol.crypto import HeaderHash
from jam.types.work.report import WorkReport
from jam.utils.constants import SLOT_PERIOD, GENESIS_TS
from jam.operations.tranche_store import EncodedWR, JudgmentRecord, Tranche, TrancheState, TrancheStore, tranche_store



# Logger for Auditing module
logger = get_logger("audit")

class AuditEngine():
    """
    Audit (tranche) engine: after each block (each timeslot), kick off
    the tranche-by-tranche auditing process.
    """

    @classmethod
    async def run(cls, header_hash: HeaderHash):
        from jam.network.node import node

        # Ensure network is up
        if not node.is_initialized:
            logger.debug("Network not initialized – skipping audit")
            return

        raw_list = sample_work_reports_with_nulls( "jam/combine.json",total_items=10, null_count=0)
        unaudited_list=TypedVector[WorkReport]([wr for wr in raw_list if wr is not None])

        valid_set = TypedVector[WorkReport]([])
        invalid_set = TypedVector[WorkReport]([])
        judgments = Dictionary[EncodedWR, JudgmentRecord]({})
        initTranche=Tranche(header_hash=header_hash,tranche_index=TrancheIndex(0))
        tranche_state=TrancheState(
            unaudited_list=unaudited_list,
            judgments=judgments,
            valid_set=valid_set,
            invalid_set=invalid_set)

        # Build a store for this slot's audit tranches
        tranche_store._save_state(initTranche,tranche_state)

        # Instantiate the core tranche engine
        engine = TrancheEngine()
        engine.run(header_hash=header_hash)

        # Completed auditing for this slot
        logger.info(f"Finished auditing header {header_hash}")
