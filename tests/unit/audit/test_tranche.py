import asyncio
# import tempfile
import math

# import jam.settings
# from jam.state.ghost import GhostState
# from jam.state.state import setup_state
# from rockstore import RockStore

from jam.audit.tranche_engine import TrancheEngine
from jam.operations.tranche_store import EncodedWR, Tranche, TrancheState, JudgmentRecord, TrancheStore,tranche_store
from jam.types.protocol.core import TrancheIndex
from jam.types.protocol.crypto import HeaderHash
from jam.types.work.report import WorkReport, WorkReportHash
from tsrkit_types.sequences import TypedVector
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.integers import Uint

from datetime import datetime

from jam.logging import get_logger
from jam.utils.constants import AUDIT_PERIOD
from tests.unit.audit.test_tranche_store import another_dummy_work_report, dummy_work_report

logger = get_logger("tranche_test")

def create_test_tranche_state() -> TrancheState:
    """
    Create a TrancheState with 2 WRs for testing:
    - wr1 with dummy judgments (treated as likely valid)
    - wr2 with empty judgments (treated as pending/unaudited)
    """
    wr1 = dummy_work_report()
    wr2 = another_dummy_work_report()

    unaudited_list = TypedVector[WorkReport]([wr1, wr2])
    judgments = Dictionary[EncodedWR, JudgmentRecord]({
        wr1.encode(): JudgmentRecord.dummy(),
        wr2.encode(): JudgmentRecord.dummy()
    })
    valid_set = TypedVector[WorkReport]([])
    invalid_set = TypedVector[WorkReport]([])

    return TrancheState(
        unaudited_list=unaudited_list,
        judgments=judgments,
        valid_set=valid_set,
        invalid_set=invalid_set
    )

async def test_tranche_engine():
    """
    Full test for TrancheEngine:
    - Initializes jam.settings and state in a temp dir
    - Creates initial TrancheState
    - Runs TrancheEngine
    - Prints final state for verification
    """


    header_hash=HeaderHash(b'header_hash_1'.ljust(32, b'\0'))
    tranche_index = TrancheIndex(0)

    tranche = Tranche(tranche_index=tranche_index, header_hash=header_hash)
    init_time=datetime.now()
    initial_state = create_test_tranche_state()
    # store=TrancheStore()
    tranche_store._save_state(tranche, initial_state)
    logger.info("✅ Initial TrancheState saved for testing.")

    # Run the TrancheEngine
    engine = TrancheEngine()
    await engine.run(header_hash=header_hash)

    # # Load and print final state for verification
    # updated_tranche_index = math.ceil(
    #     (datetime.now() - init_time).total_seconds() / AUDIT_PERIOD
    # )
    # tranche = Tranche(tranche_index=TrancheIndex(updated_tranche_index), header_hash=header_hash)
    # final_state = tranche_store._get_state(tranche)

    # print("\n✅ Final TrancheState after TrancheEngine run:")
    # print(f"Valid WRs: {[wr.hex()[:16] for wr in final_state.valid_set]}")
    # print(f"Invalid WRs: {[wr.hex()[:16] for wr in final_state.invalid_set]}")
    # print(f"Remaining unaudited WRs: {[wr.hex()[:16] for wr in final_state.unaudited_list]}")

if __name__ == "__main__":
    asyncio.run(test_tranche_engine())
