import asyncio
import os

import pytest


from jam.audit.tranche_engine import TrancheEngine
from jam.storage.tranche_store import Tranche, TrancheState, AuditRecord, ValidatorList,tranche_store
from jam.types.protocol.core import TrancheIndex, ValidatorIndex
from jam.types.protocol.crypto import Hash, HeaderHash
from jam.types.work.report import WorkReportHash
from tsrkit_types.sequences import TypedVector
from tsrkit_types.dictionary import Dictionary

from datetime import datetime

from jam.logging import get_logger
from tests.unit.audit.test_tranche_store import another_dummy_work_report, dummy_work_report

logger = get_logger("tranche_test")


def create_test_tranche_state() -> TrancheState:
    """
    Create a TrancheState with 2 WRs for testing:
    - wr1 with dummy judgments (treated as likely valid)
    - wr2 with empty judgments (treated as pending/unaudited)
    """
    wr_hash1 = WorkReportHash(Hash.blake2b(dummy_work_report().encode()))
    wr_hash2 = WorkReportHash(Hash.blake2b(another_dummy_work_report().encode()))
    dummy_judgements1=AuditRecord.dummy()
    dummy_judgements2=AuditRecord.dummy()
    dummy_judgements2.true_votes=ValidatorList([ValidatorIndex(0),ValidatorIndex(1),ValidatorIndex(2),ValidatorIndex(3),ValidatorIndex(4),ValidatorIndex(5)])
    dummy_judgements2.false_votes=ValidatorList([])
    unaudited_list = TypedVector[WorkReportHash]([wr_hash1, wr_hash2])
    judgments = Dictionary[WorkReportHash, AuditRecord]({
        wr_hash1: dummy_judgements1,
        wr_hash2: dummy_judgements2
    })
    valid_set = TypedVector[WorkReportHash]([])
    invalid_set = TypedVector[WorkReportHash]([])

    return TrancheState(
        unaudited_list=unaudited_list,
        judgments=judgments,
        valid_set=valid_set,
        invalid_set=invalid_set,
    )

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
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
    # create_test_tranche_state()
