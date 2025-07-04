from jam.audit import utils
import jam.settings
import tempfile
import json
import random
import time

from jam.state.ghost import GhostState
from jam.state.state import setup_state
from jam.types import state
from jam.types.protocol.core import CoreIndex
from jam.types.work.report import WorkReport
from jam.utils.constants import VALIDATOR_COUNT

def populate_db(db, wr_list, tranche):
    """
    Populates the database with dummy data for announcements and judgements per tranche.
    Refer to Section 17.1 for auditing process.
    """
    for wr in wr_list:
        announced = list(range(random.randint(2, 6)))  # 0..5 validators
        # true_judgements = random.sample(announced, random.randint(3, 6))
        sample_validator_size = random.randint(2, len(announced))
        true_judgements= random.sample(announced, sample_validator_size)
        false_judgements = [v for v in announced if v not in true_judgements]

        db.put(f'announcement:{wr.encode()}:{tranche}'.encode(), json.dumps(announced).encode())
        db.put(f'judgement_true:{wr.encode()}:{tranche}'.encode(), json.dumps(true_judgements).encode())
        db.put(f'judgement_false:{wr.encode()}:{tranche}'.encode(), json.dumps(false_judgements).encode())

def An(db, wr: WorkReport, tranche: int) -> list:
    """
    Retrieves validators who announced a work-report for a given tranche.
    Refer to Eq. 17.11.
    """
    key = f'announcement:{wr.encode()}:{tranche}'.encode()
    value = db.get(key)
    return json.loads(value.decode()) if value else []

def J_t(db, wr: WorkReport, tranche: int) -> list:
    """
    Retrieves validators who gave a true judgment for a work-report in a given tranche.
    Refer to Eq. 17.12.
    """
    key = f'judgement_true:{wr.encode()}:{tranche}'.encode()
    value = db.get(key)
    return json.loads(value.decode()) if value else []

def J_f(db, wr: WorkReport, tranche: int) -> list:
    """
    Retrieves validators who gave a false judgment for a work-report in a given tranche.
    Refer to Eq. 17.12.
    """
    key = f'judgement_false:{wr.encode()}:{tranche}'.encode()
    value = db.get(key)
    return json.loads(value.decode()) if value else []

# def dummy_vrf_check(wr: WorkReport, tranche: int) -> bool:
#     """
#     Dummy VRF check for auditing condition (30% chance of True).
#     Should use bandersnatch_y function on s_0 as per Eq. 17.3 and 17.15.
#     """
#     return random.random() < 0.3

def audit_condition(db, work_report: WorkReport, tranche_index: int) -> bool | None:
    """
    Evaluates the audit condition for a work-report in a given tranche.
    - True: Audited (no false judgments and announcements match true judgments, or 2/3 supermajority true).
    - False: Failed (more than 1/3 false judgments).
    - None: Inconclusive, proceed to next tranche.
    Refer to Eq. 17.19.
    """
    false_count = len(J_f(db, work_report, tranche_index))
    true_count = len(J_t(db, work_report, tranche_index))
    announced_count = len(An(db, work_report, tranche_index))
    # print("announce_count",announced_count,"true_count",true_count,"false_count",false_count,"condition",(false_count == 0 and announced_count == true_count) or true_count >= (2 / 3) * VALIDATOR_COUNT,"VALIDATOR_COUNT",VALIDATOR_COUNT)
    if (false_count == 0 and announced_count == true_count) or true_count >= (2 / 3) * VALIDATOR_COUNT:
        return True
    elif false_count > (1 / 3) * VALIDATOR_COUNT:
        return False
    return None

def dummy_wrs(core_range: int) -> list[WorkReport]:
    """
    Generates dummy work-reports for the specified number of cores.
    """
    wrs = []
    for core_index in range(core_range):
        dummy_wr = WorkReport.empty()
        dummy_wr.core_index = CoreIndex(core_index)
        wrs.append(dummy_wr)
    return wrs

def test_tranche():
    """
    Tests the auditing process for work-reports across tranches, evaluating three criteria:
    1. Audited: No next tranche needed.
    2. Inconclusive: Proceed to next tranche.
    3. Failed: No next tranche needed.
    Refer to Section 17.2.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        jam.settings.setup_setting(data_path=tmpdir, seed=0)
        db = jam.settings.settings.main_db
        setup_state(db, GhostState.genesis())

        all_wrs = dummy_wrs(5)  # Generate 5 dummy work-reports
        audited_wrs = set()  # Successfully audited WRs
        failed_wrs = set()   # Failed WRs
        tranche = 0
        max_tranches = 10

        while tranche < max_tranches:
            print(f"\n=== Tranche {tranche} ===")
            wrs_to_audit = [wr for wr in all_wrs if wr.encode() not in audited_wrs and wr.encode() not in failed_wrs]
            if not wrs_to_audit:
                print("✅ All WRs either audited or failed.")
                break

            populate_db(db, wrs_to_audit, tranche)

            for wr in wrs_to_audit:
                announced = An(db, wr, tranche)
                true_judged = J_t(db, wr, tranche)
                false_judged = J_f(db, wr, tranche)

                # print(f"  Announced by: {announced}")
                # print(f"  True Judgements: {true_judged}")
                # print(f"  False Judgements: {false_judged}")

                audit_result = audit_condition(db, wr, tranche)
                if audit_result is True:
                    audited_wrs.add(wr.encode())
                    print(f"✅ WR {wr.encode().hex()} audited in tranche {tranche}.")
                elif audit_result is False:
                    failed_wrs.add(wr.encode())
                    print(f"❌ WR {wr.encode().hex()} failed in tranche {tranche}.")
                else:
                    print(f"⏳ WR {wr.encode().hex()} inconclusive in tranche {tranche}, will retry in next tranche.")

            tranche += 1
            time.sleep(2)  # Simulate time between tranches

        print("\n=== Audit Summary ===")
        if len(audited_wrs) == len(all_wrs):
            print("🎉 All WRs successfully audited!")
        else:
            print(f"✅ Audited WRs: {[wr.core_index for wr in all_wrs if wr.encode() in audited_wrs]}")
            print(f"❌ Failed WRs: {[wr.core_index for wr in all_wrs if wr.encode() in failed_wrs]}")
            print(f"⚠️ Inconclusive WRs: {[wr.core_index for wr in all_wrs if wr.encode() not in audited_wrs and wr.encode() not in failed_wrs]}")

if __name__ == "__main__":
    test_tranche()
