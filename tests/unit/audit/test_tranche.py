

from asyncio.timeouts import timeout
from datetime import datetime, time, timezone
import re
from typing import List, Dict, Tuple, Optional
# import pytest  # Commented out for simple testing
from unittest.mock import patch, MagicMock
import time as time_module
import threading
from dataclasses import dataclass

from tsrkit_types import Null, Option

from jam.assurances.assurances import Assurances
# from jam.config.data_stores import DataStores
# from jam.state.ghost import GhostState
# from jam.state.state import State, setup_state
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

from jam.utils.constants import CORE_COUNT, VALIDATOR_COUNT, AUDIT_PERIOD, SLOT_PERIOD
from jam.utils.dummy.dummy_block import create_dummy_block
from jam.utils.dummy.dummy_extrinsics import create_dummy_work_report
from jam.utils.dummy.utils import create_dummy_bytes, create_dummy_bytes32

# Mock constants
MOCK_SLOT_PERIOD = 6
MOCK_AUDIT_PERIOD = 8



class AuditMemoryStore:
    """
    A class to simulate a database for tranche-indexed judgments and announcements.
    Stores judgments of work reports existing in each tranche and announcements made for those work reports.
    """
    def __init__(self):
        """Initializes the in-memory 'databases'."""
        # Structure: {tranche_index: {'judgments': {wr_hash: {validator_index: judgment}}, 'announcements': {validator_index: announcement}}}
        self._store = {}

    def save_announcement(self, tranche_index: int, validator_index: int, announcement: str): # for now keeping it as string later on sign bytes
        """Stores an announcement given for work reports in a tranche indexed manner."""
        self._store.setdefault(tranche_index, {'judgments': {}, 'announcements': {}})
        self._store[tranche_index]['announcements'][validator_index] = announcement
        print(f"STORED Announcement: Tranche={tranche_index}, Validator={validator_index}")

    def save_judgment(self, tranche_index: int, wr_hash: bytes, validator_index: int, judgment: str):
        """Stores a judgment under a specific tranche index and WR."""
        self._store.setdefault(tranche_index, {'judgments': {}, 'announcements': {}})
        self._store[tranche_index]['judgments'].setdefault(wr_hash, {})
        self._store[tranche_index]['judgments'][wr_hash][validator_index] = judgment
        print(f"STORED Judgment: Judgment={judgment} Tranche={tranche_index}, Validator={validator_index} for WR='{wr_hash.decode()}'")

    def get_announcements_for_tranche(self, tranche_index: int) -> dict:
        """Fetches all announcements indexed by tranche."""
        return self._store.get(tranche_index, {}).get('announcements', {})

    def get_judgments_for_wr(self, tranche_index: int, wr_hash: bytes) -> dict:
        """Fetches all judgments for a specific WR, indexed by tranche."""
        return self._store.get(tranche_index, {}).get('judgments', {}).get(wr_hash, {})

    def clear(self):
        """Clears all stored data."""
        self._store.clear()
        print("CLEARED the AuditMemoryStore.")



@dataclass
class TrancheState:
    """Represents the state of a tranche with work reports and audit statuses."""
    tranche_index: int
    work_reports: List[bytes]
    announcements: Dict[int, any]
    judgments: Dict[bytes, Dict[int, str]]
    start_time: float
    audit_completed: bool = False

tranche_states: Dict[int, TrancheState] = {}

def check_tranche_audit_completion(audit_db: AuditMemoryStore, tranche_n: int) -> bool:
    counts = fetch_judgments_and_announcements_count(audit_db, tranche_n)
    if counts['judgments'] < counts['announcements']:
        print(f"Tranche {tranche_n} has incomplete judgments: {counts['judgments']} < {counts['announcements']}")
        return False
    if check_for_negative_judgments(audit_db, tranche_n):
        print(f"Tranche {tranche_n} has INVALID judgments.")
        return False
    return True

def fetch_judgments_and_announcements_count(audit_db: AuditMemoryStore, tranche_n: int) -> Dict[str, int]:
    """
    Function to fetch how many judgments and announcements are there for tranche n.

    Args:
        audit_db: The audit database store
        tranche_n: The tranche index to check

    Returns:
        Dictionary with counts of judgments and announcements
    """
    announcements = audit_db.get_announcements_for_tranche(tranche_n)
    announcement_count = len(announcements)

    # Count total judgments across all work reports in this tranche
    tranche_data = audit_db._store.get(tranche_n, {})
    all_judgments = tranche_data.get('judgments', {})

    total_judgment_count = 0
    for wr_hash, wr_judgments in all_judgments.items():
        total_judgment_count += len(wr_judgments)

    return {
        'announcements': announcement_count,
        'judgments': total_judgment_count,
        'work_reports': len(all_judgments)
    }


def check_for_negative_judgments(audit_db: AuditMemoryStore, tranche_n: int) -> bool:
    """
    Function to check if there are any negative (INVALID) judgments in tranche n.

    Args:
        audit_db: The audit database store
        tranche_n: The tranche index to check

    Returns:
        True if any negative judgments found, False otherwise
    """
    tranche_data = audit_db._store.get(tranche_n, {})
    all_judgments = tranche_data.get('judgments', {})

    for wr_hash, wr_judgments in all_judgments.items():
        for validator_idx, judgment in wr_judgments.items():
            if judgment == "INVALID":
                print(f"  Found INVALID judgment from validator {validator_idx} for WR {wr_hash.decode()}")
                return True

    return False


import random

def tranche_audit_loop():
    """
    Tranche audit loop:
    - Retains WRs that are not yet audited for next tranche.
    - Removes WRs that have been audited successfully.
    - Skips already audited WRs explicitly in each tranche.
    - Stops when all WRs are audited or max tranches reached.
    """
    tranche_attempts = 0
    max_tranches = 5
    validators = [0, 1, 2, 3, 4, 5]
    audit_db = AuditMemoryStore()

    def get_initial_wr_list():
        return [f'wr_hash_{i}'.encode() for i in range(1, 6)]  # 5 WRs

    wr_list = get_initial_wr_list()
    wr_audit_status = {wr: False for wr in wr_list}

    audited_wrs_per_tranche = {}

    while tranche_attempts < max_tranches:
        tranche_n = tranche_attempts
        print(f"\n=== Tranche {tranche_n} ===")
        print(f"Current WR audit status: { {wr.decode(): status for wr, status in wr_audit_status.items()} }")

        wrs_to_audit = [wr for wr, audited in wr_audit_status.items() if not audited]
        if not wrs_to_audit:
            print("✅ All WRs audited successfully.")
            break

        skipped_wrs = [wr.decode() for wr, audited in wr_audit_status.items() if audited]
        if skipped_wrs:
            print(f"⏭️ Skipping already audited WRs: {skipped_wrs}")

        # Announcements
        for validator_idx in validators:
            announcement = f"Announcement for tranche {tranche_n} by validator {validator_idx}"
            audit_db.save_announcement(tranche_n, validator_idx, announcement)

        # Judgments
        for wr_hash in wrs_to_audit:
            for validator_idx in validators:
                chance = random.random()
                if chance < 0.82:
                    judgment = "VALID"
                elif chance < 0.98:
                    judgment = "INVALID"
                else:
                    continue  # No vote
                audit_db.save_judgment(tranche_n, wr_hash, validator_idx, judgment)

        # Check WR audit status
        announcements = audit_db.get_announcements_for_tranche(tranche_n)
        announcement_count = len(announcements)
        tranche_audited_wrs = []

        for wr_hash in wrs_to_audit:
            judgments = audit_db.get_judgments_for_wr(tranche_n, wr_hash)
            judgment_count = len(judgments)
            has_invalid = "INVALID" in judgments.values()

            print(f"WR {wr_hash.decode()} | Judgments: {judgment_count}, Announcements: {announcement_count}, INVALID: {has_invalid}")

            if judgment_count == announcement_count and not has_invalid:
                print(f"✅ WR {wr_hash.decode()} audited successfully.")
                wr_audit_status[wr_hash] = True
                tranche_audited_wrs.append(wr_hash.decode())
            else:
                print(f"❌ WR {wr_hash.decode()} requires re-audit in next tranche.")

        audited_wrs_per_tranche[tranche_n] = tranche_audited_wrs

        tranche_attempts += 1
        time_module.sleep(1)  # Simulate waiting

    # Final summary
    print("\n=== Audit Summary ===")
    for tranche, wrs in audited_wrs_per_tranche.items():
        print(f"Tranche {tranche} audited WRs: {wrs}")

    failed_wrs = [wr.decode() for wr, audited in wr_audit_status.items() if not audited]
    if failed_wrs:
        print(f"\n❌ Audit incomplete for WRs after {max_tranches} tranches:")
        for wr in failed_wrs:
            print(f" - {wr}")
    else:
        print(f"\n✅ All WRs audited successfully within {tranche_attempts} tranches.")

    return audit_db


def test_audit_store_usage():
    """
    An example test demonstrating how to use the AuditMemoryStore class
    with the new tranche-indexed structure.
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

def test_tranche_audit_flow():
    """
    Improved test flow:
    - Prints a clear summary for each tranche.
    - Shows WR-level status: vote counts, INVALID flags.
    - Provides a final clear summary if any WRs failed.
    """
    print("\n=== Testing Improved Tranche Audit Flow with Summary ===")

    # Run the tranche audit loop
    audit_db = tranche_audit_loop()

    for tranche_n in range(5):  # Check up to 5 tranches as in your loop
        print(f"\n--- Tranche {tranche_n+1} Summary ---")
        counts = fetch_judgments_and_announcements_count(audit_db, tranche_n)
        print(f"Total Announcements: {counts['announcements']}")
        print(f"Total Judgments: {counts['judgments']}")
        print(f"Total Work Reports: {counts['work_reports']}")

        tranche_data = audit_db._store.get(tranche_n, {})
        wr_judgments = tranche_data.get('judgments', {})

        if not wr_judgments:
            print("⚠️ No WR judgments found in this tranche.")
            continue

        for wr_hash, validator_votes in wr_judgments.items():
            vote_count = len(validator_votes)
            has_invalid = any(judgment == "INVALID" for judgment in validator_votes.values())
            print(f"WR: {wr_hash.decode()} | Votes: {vote_count} | INVALID: {has_invalid}")

            if vote_count < counts['announcements'] or has_invalid:
                print(f"❌ {wr_hash.decode()} needs re-audit.")
            else:
                print(f"✅ {wr_hash.decode()} audited successfully in this tranche.")

    # Final check for incomplete WRs
    tranche_summary = {}
    for tranche_n, tranche_data in audit_db._store.items():
        for wr_hash, validator_votes in tranche_data.get('judgments', {}).items():
            vote_count = len(validator_votes)
            has_invalid = any(judgment == "INVALID" for judgment in validator_votes.values())
            if vote_count < len(tranche_data.get('announcements', {})) or has_invalid:
                tranche_summary[wr_hash.decode()] = "FAILED"
            else:
                tranche_summary[wr_hash.decode()] = "AUDITED"

    failed_wrs = [wr for wr, status in tranche_summary.items() if status == "FAILED"]

    if failed_wrs:
        print("\n❌ Audit did not complete successfully for the following WRs:")
        for wr in failed_wrs:
            print(f"  - {wr}")
    else:
        print("\n✅ All WRs audited successfully across all tranches.")

    return audit_db


def print_audit_database_structure(audit_db: AuditMemoryStore):
    """
    Helper function to print the complete structure of the audit database.
    Shows the format: n:(Judgements, Announcements)
    """
    print("\n=== Audit Database Structure ===")
    print("Format: tranche_index:(Judgements of WRs, Announcements)")

    for tranche_idx, tranche_data in audit_db._store.items():
        print(f"\nTranche {tranche_idx}:")

        # Print announcements
        announcements = tranche_data.get('announcements', {})
        print(f"  Announcements ({len(announcements)}):")
        for validator_idx, announcement in announcements.items():
            print(f"    Validator {validator_idx}: {announcement}")

        # Print judgments
        judgments = tranche_data.get('judgments', {})
        print(f"  Judgments for {len(judgments)} work reports:")
        for wr_hash, wr_judgments in judgments.items():
            print(f"    {wr_hash.decode()}:")
            for validator_idx, judgment in wr_judgments.items():
                print(f"      Validator {validator_idx}: {judgment}")


if __name__ == "__main__":
    print("=== Demonstrating Focused Tranche Audit Flow ===")

    # # Run the focused tranche test
    # print("\n1. Running focused tranche loop test...")
    # test_focused_tranche_loop()

    print("\n2. Running full tranche audit loop...")
    audit_db = tranche_audit_loop()

    # Print the database structure
    print_audit_database_structure(audit_db)

    print("\n3. Running basic store test...")
    test_audit_store_usage()
    print("\nBasic test passed!")

    print("\n4. Running complete tranche flow test...")
    test_tranche_audit_flow()
    print("\nTranche audit flow test passed!")

    print("\n=== All tests completed successfully! ===")
    print("\nKey Features Demonstrated:")
    print("- Tranche n starts from 0 and increases every 8 seconds")
    print("- DB stores judgments and announcements indexed by tranche")
    print("- Fetch function counts judgments and announcements per tranche")
    print("- Check function detects negative judgments")
    print("- System continues looping when negative judgments found")


# Flow
# DummyState(block)->STFs->Auditing(state,assuranceList)->Grandpa
