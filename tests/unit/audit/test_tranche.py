import asyncio
import tempfile

import jam.settings

# from jam.state.ghost import GhostState
# from jam.state.state import setup_state
import math
from rockstore import RockStore

from jam.audit.tranche_engine import TrancheEngine
from jam.audit.tranche import Tranche, TrancheState, JudgmentRecord, TrancheStore
from jam.types.work.report import WorkReportHash
from tsrkit_types.sequences import TypedVector
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.integers import Uint

from datetime import datetime

from jam.logging import get_logger
from jam.utils.constants import AUDIT_PERIOD

logger = get_logger("tranche_test")


def create_test_tranche_state() -> TrancheState:
    """
    Create a TrancheState with 2 WRs for testing:
    - wr1 with dummy judgments (treated as likely valid)
    - wr2 with empty judgments (treated as pending/unaudited)
    """
    wr1 = WorkReportHash(b"wr1_hash_32_bytes______00000000")
    wr2 = WorkReportHash(b"wr2_hash_32_bytes______00000000")

    unaudited_list = TypedVector[WorkReportHash]([wr1, wr2])
    print("Unaudited Work Reports:", unaudited_list)
    judgments = Dictionary[WorkReportHash, JudgmentRecord](
        {wr1: JudgmentRecord.dummy(), wr2: JudgmentRecord.dummy()}
    )

    valid_set = TypedVector[WorkReportHash]([])
    invalid_set = TypedVector[WorkReportHash]([])

    return TrancheState(
        unaudited_list=unaudited_list,
        judgments=judgments,
        valid_set=valid_set,
        invalid_set=invalid_set,
    )


async def test_tranche_engine():
    """
    Full test for TrancheEngine:
    - Initializes jam.settings and state in a temp dir
    - Creates initial TrancheState
    - Runs TrancheEngine
    - Prints final state for verification
    """

    slot_index = Uint(0)
    tranche_index = Uint(0)

    tranche = Tranche(tranche_index=Uint(tranche_index), slot_index=Uint(slot_index))
    init_time = datetime.now()
    initial_state = create_test_tranche_state()
    store = TrancheStore()
    store.save(tranche, initial_state)

    logger.info("✅ Initial TrancheState saved for testing.")

    # Run the TrancheEngine
    engine = TrancheEngine(store=store)
    await engine.run(slot_index=slot_index)

    # Load and print final state for verification
    updated_tranche_index = math.ceil(
        (datetime.now() - init_time).total_seconds() / AUDIT_PERIOD
    )
    tranche = Tranche(
        tranche_index=Uint(updated_tranche_index), slot_index=Uint(slot_index)
    )
    final_state = store.load(tranche)

    print("\n✅ Final TrancheState after TrancheEngine run:")
    print(f"Valid WRs: {[wr.hex()[:16] for wr in final_state.valid_set]}")
    print(f"Invalid WRs: {[wr.hex()[:16] for wr in final_state.invalid_set]}")
    print(
        f"Remaining unaudited WRs: {[wr.hex()[:16] for wr in final_state.unaudited_list]}"
    )


if __name__ == "__main__":
    asyncio.run(test_tranche_engine())
