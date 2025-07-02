from jam.audit import utils
import jam.settings
import tempfile
import json
import random
import time

def populate_db(db, wr_list, tranche):
    """
    Populates the database with dummy data for announcements and judgements per tranche.
    """
    for wr in wr_list:
        announced = list(range(6))  # 0..5 validators
        true_judgements = random.sample(announced, random.randint(3, 6))
        false_judgements = [v for v in announced if v not in true_judgements]

        db.put(f'announcement:{wr}:{tranche}'.encode(), json.dumps(announced).encode())
        db.put(f'judgement_true:{wr}:{tranche}'.encode(), json.dumps(true_judgements).encode())
        db.put(f'judgement_false:{wr}:{tranche}'.encode(), json.dumps(false_judgements).encode())

def An(db, wr, tranche):
    key = f'announcement:{wr}:{tranche}'.encode()
    value = db.get(key)
    if value:
        return json.loads(value.decode())
    return []

def J_t(db, wr, tranche):
    key = f'judgement_true:{wr}:{tranche}'.encode()
    value = db.get(key)
    if value:
        return json.loads(value.decode())
    return []

def J_f(db, wr, tranche):
    key = f'judgement_false:{wr}:{tranche}'.encode()
    value = db.get(key)
    if value:
        return json.loads(value.decode())
    return []

def dummy_vrf_check(wr, tranche):
    """
    Dummy VRF: returns True with 30% chance, else False.
    """

    vrf=utils.bandersnatch_y(bytes)
    # return random.random() < 0.3

# if __name__ == "__main__":
#     with tempfile.TemporaryDirectory() as tmpdir:
#         jam.settings.setup_setting(data_path=tmpdir, seed=0)
#         db = jam.settings.settings.main_db

#         all_wrs = ['wr1', 'wr2', 'wr3', 'wr4', 'wr5']
#         audited_wrs = set()
#         tranche = 0
#         max_tranches = 10

#         while tranche < max_tranches:
#             print(f"\n=== Tranche {tranche} ===")
#             wrs_to_audit = [wr for wr in all_wrs if wr not in audited_wrs]
#             if not wrs_to_audit:
#                 print("✅ All WRs audited successfully.")
#                 break

#             populate_db(db, wrs_to_audit, tranche)

#             for wr in wrs_to_audit:
#                 announced = An(db, wr, tranche)
#                 true_judged = J_t(db, wr, tranche)
#                 false_judged = J_f(db, wr, tranche)

#                 print(f"\nWR: {wr}")
#                 print(f"  Announced by: {announced}")
#                 print(f"  True Judgements: {true_judged}")
#                 print(f"  False Judgements: {false_judged}")

#                 # Auditing condition:
#                 # - No false judgements
#                 # - OR dummy_vrf_check returns True
#                 if len(false_judged) == 0 or dummy_vrf_check(wr, tranche):
#                     audited_wrs.add(wr)
#                     print(f"✅ WR {wr} audited in tranche {tranche}.")
#                 else:
#                     print(f"❌ WR {wr} NOT audited in tranche {tranche}, will retry in next tranche.")

#             tranche += 1
#             time.sleep(2)  # Simulate time between tranches

#         if len(audited_wrs) == len(all_wrs):
#             print("\n🎉 All WRs successfully audited across all tranches!")
#         else:
#             failed_wrs = [wr for wr in all_wrs if wr not in audited_wrs]
#             print("\n⚠️ Audit did not complete for the following WRs:")
#             for wr in failed_wrs:
#                 print(f"  - {wr}")



if __name__ == "__main__":
    bytes=b"bytes bhai"

    for i in range(10):
        vrf_bytes=utils.bandersnatch_y(bytes)
        print(vrf_bytes[i])
    # print("All tests passed!",vrf_bytes[i])
