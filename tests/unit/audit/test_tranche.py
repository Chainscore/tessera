from asyncio.timeouts import timeout
from datetime import datetime, time, timezone
import re
from typing import List
import pytest
from unittest.mock import patch, MagicMock

from sympy.core.logic import Optional
from sympy.ntheory.factor_ import core
from sympy.physics.units.systems.si import newton
from tsrkit_types import Null, Option

from jam.assurances.assurances import Assurances
from jam.config.data_stores import DataStores
from jam.audit.audit import AuditingAndJudgement
from jam.state.ghost import GhostState
from jam.state.state import State, setup_state
from jam.types.block import Header
from jam.types.block import block
from jam.types.block.block import Block
from jam.types.state.kappa import Kappa
from jam.types.state.rho import OptionalWorkReportState, Rho, WorkReportState
from jam.types.work.report import WorkReport
from jam.types.protocol.core import TimeSlot, ValidatorIndex, CoreIndex
from jam.types.protocol.crypto import Hash, BandersnatchPublic, Ed25519Public, BlsPublic
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U16, U8, Uint
from jam.types.protocol.validators import (
    IPAddress,
    ValidatorData,
    ValidatorMetadata,
)
import tempfile

from jam.utils.constants import CORE_COUNT, VALIDATOR_COUNT
from jam.utils.dummy.dummy_block import create_dummy_block
from jam.utils.dummy.dummy_extrinsics import create_dummy_work_report
from jam.utils.dummy.utils import create_dummy_bytes, create_dummy_bytes32

# Mock constants
MOCK_SLOT_PERIOD = 6
MOCK_AUDIT_PERIOD = 8

class AuditMemoryStore:
  """
  A class to simulate a database for audit announcements and judgments.
  This provides a clean API for saving and fetching audit-related data
  for testing purposes.
  """
  def __init__(self):
    """Initializes the in-memory 'databases'."""
    # Structure: {tranche_index: {validator_index: announcement}}
    self._announcements = {}
    # Structure: {tranche_index: {wr_hash: {validator_index: judgment}}}
    self._judgments = {}

  def save_announcement(self, tranche_index: int, validator_index: int, announcement: any):
    """Saves a validator's announcement for a specific tranche."""
    self._announcements.setdefault(tranche_index, {})
    self._announcements[tranche_index][validator_index] = announcement
    print(f"STORED Announcement: Tranche={tranche_index}, Validator={validator_index}")

  def save_judgment(self, tranche_index: int, wr_hash: bytes, validator_index: int, judgment: str):
   """Saves a validator's judgment for a specific Work-Report in a tranche."""
   self._judgments.setdefault(tranche_index, {})
   self._judgments[tranche_index].setdefault(wr_hash, {})
   self._judgments[tranche_index][wr_hash][validator_index] = judgment
   print(f"STORED Judgment: Tranche={tranche_index}, Validator={validator_index} for WR='{wr_hash.decode()}'")

  def get_announcements_for_tranche(self, tranche_index: int) -> dict:
    """Fetches all announcements for a given tranche."""
    return self._announcements.get(tranche_index, {})

  def get_judgments_for_wr(self, tranche_index: int, wr_hash: bytes) -> dict:
    """Fetches all judgments for a specific Work-Report in a tranche."""
    return self._judgments.get(tranche_index, {}).get(wr_hash, {})

  def get_all_judgments_for_tranche(self, tranche_index: int) -> dict:
    """Fetches all judgments across all WRs for a given tranche."""
    return self._judgments.get(tranche_index, {})

  def clear(self):
    """Clears all data from the store."""
    self._announcements.clear()
    self._judgments.clear()
    print("CLEARED the AuditMemoryStore.")



def test_audit_store_usage():
    """
    An example test demonstrating how to use the AuditMemoryStore class.
    """

    # 1. ARRANGE
    audit_db = AuditMemoryStore()

    tranche_0 = 0
    validator_3 = 3
    validator_5 = 5
    wr_hash_A = b'work_report_hash_A'
    wr_hash_B = b'work_report_hash_B'

    # 2. ACT
    audit_db.save_announcement(tranche_0, validator_3, {"dummy_announcement_v3"})
    audit_db.save_announcement(tranche_0, validator_5, {"dummy_announcement_v5"})

    audit_db.save_judgment(tranche_0, wr_hash_A, validator_3, "VALID")
    audit_db.save_judgment(tranche_0, wr_hash_A, validator_5, "VALID")
    audit_db.save_judgment(tranche_0, wr_hash_B, validator_3, "INVALID")

    # 3. ASSERT

    # Verify announcements
    all_announcements_t0 = audit_db.get_announcements_for_tranche(tranche_0)
    assert len(all_announcements_t0) == 2
    assert all_announcements_t0[validator_5] == {"dummy_announcement_v5"}

    # Verify judgments for WR_A
    judgments_for_wr_A = audit_db.get_judgments_for_wr(tranche_0, wr_hash_A)
    assert len(judgments_for_wr_A) == 2
    assert judgments_for_wr_A[validator_3] == "VALID"

    # Verify judgments for a non-existent WR
    judgments_for_wr_C = audit_db.get_judgments_for_wr(tranche_0, b'non_existent_wr')
    assert judgments_for_wr_C == {}



@pytest.fixture
def mock_state():
    return create_mock_state()

@patch('jam.audit.audit.CURRENT_TIME')
def test_tranche_creation_and_progression(mock_state):
    """Test audit tranche lifecycle."""
    time_now=datetime.now(timezone.utc)
    finalized_block_creation_time = 10
    finalized_header = Header(slot=0, parent=Hash(bytes(32)), parent_state_root=Hash(bytes(32)), extrinsic_hash=Hash(bytes(32)))

    # Instantiate the class we are testing, providing the mock state and an empty set for assurances.
    new_wr_list=dummy_new_wr_list()
    Auditing = AuditingAndJudgement(current_state=mock_state, current_assurances=new_wr_list)
    q=Auditing.report_to_be_audit()
    header=create_dummy_header()
    # tranche=generate_tranche_index(header=header)
    tranche=0
    for wr in q:
        # tranche=tranche # It will be wr specific
        annuncements=validator_announcement_statement(header=header,ValidatorIndex=0)

    return new_wr_list



def dummy_new_wr_list()->List[WorkReport]:
    pre_auditing_report: List[WorkReport] = []
    work_report=[1,2,3] # List of WP from the dummy work-packages
    # for i, (report, _slot) in enumerate(state.rho):
    #     if report in a:
    #         pre_auditing_report.append(report)
    return work_report

if __name__ == "__main__":
    state = create_mock_state()
    test_tranche_creation_and_progression(mock_state=state)

    print("yo")



# Flow
# DummyState(block)->STFs->Auditing(state,assuranceList)->Grandpa
