import asyncio
import tempfile

import jam.settings
from jam.state.ghost import GhostState
from jam.state.state import setup_state

from rockstore import RockStore

from jam.audit.tranche_engine import TrancheEngine
from jam.audit.tranche import Tranche, TrancheState, JudgmentRecord
from jam.types.work.report import WorkReportHash
from tsrkit_types.sequences import TypedVector
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.integers import Uint

from jam.logging import get_logger

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

    judgments = Dictionary[WorkReportHash, JudgmentRecord]({
        wr1: JudgmentRecord.dummy(),
        wr2: JudgmentRecord.dummy()
    })

    valid_set = TypedVector[WorkReportHash]([])
    invalid_set = TypedVector[WorkReportHash]([])

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

    with tempfile.TemporaryDirectory() as tmpdir:
        jam.settings.setup_setting(data_path=tmpdir, seed=0)
        db: RockStore = jam.settings.settings.main_db

        # Set up JAM initial genesis state
        setup_state(db, GhostState.genesis())

        slot_index = Uint(0)
        tranche_index = Uint(0)

        tranche = Tranche(tranche_index=Uint(tranche_index), slot_index=Uint(slot_index))
        initial_state = create_test_tranche_state()
        tranche.save_state(db, initial_state)

        logger.info("✅ Initial TrancheState saved for testing.")

        # Run the TrancheEngine
        engine = TrancheEngine(db=db)
        await engine.run(slot_index=slot_index)

        # Load and print final state for verification
        final_state = tranche.load_state(db)

        print("\n✅ Final TrancheState after TrancheEngine run:")
        print(f"Valid WRs: {[wr.hex()[:16] for wr in final_state.valid_set]}")
        print(f"Invalid WRs: {[wr.hex()[:16] for wr in final_state.invalid_set]}")
        print(f"Remaining unaudited WRs: {[wr.hex()[:16] for wr in final_state.unaudited_list]}")



if __name__ == "__main__":
    asyncio.run(test_tranche_engine())
