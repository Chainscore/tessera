# tests/unit/psiA/test_psiA.py
import json
from pathlib import Path

import pytest

# from jam.execution.host_calls.invocations.accumulate import PsiA
# from jam.types.state.delta import Delta

from tests.unit.psiA.type_psiA import TestcasePsiA, StateContext, OperandTuple, OperandTuples

# ← make sure this is importable; if not, you may need to adjust your
#    PYTHONPATH or use a relative import like:
# from .type_psiA import TestcasePsiA

# replace this with your actual host‐call function
# from jam.execution.host_calls.invocations.accumulate import PsiA


# directory where your tiny test vectors live
TEST_DATA_DIR = Path(__file__).parent / "tiny"


def load_test_vectors():
    """
    Yield one TestcasePsiA for each JSON file matching the
    'psiA*.json' pattern in the tiny/ directory.
    """
    for json_path in TEST_DATA_DIR.glob("psiA*.json"):
        data = json.loads(json_path.read_text())
        yield TestcasePsiA.from_json(data)

@pytest.mark.parametrize("vector", load_test_vectors(), ids=lambda v: v.input.slot)
def test_accumulation(vector: TestcasePsiA):
		print("vector", vector)
		# partial_state = StateContext(
		# 		service_accounts=Delta({acc.id: acc.data for acc in vector.pre_state.accounts}),
		#
		#
		# )
		# timeslot = None
		# service_id = None
		# gas = 0
		# operandTuples = OperandTuples([OperandTuple() for w in work_reports])
		# context = None
		# PsiA()