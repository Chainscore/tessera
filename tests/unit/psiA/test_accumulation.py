# tests/unit/psiA/test_psiA.py
import json
from pathlib import Path

import pytest

from jam.accumulation.accumulation import Accumulation
from jam.state.state import state
from jam.types.protocol.core import ServiceId
# from jam.accumulation.accumulation import Accumulation

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
		partial_state = StateContext(
				service_accounts=vector.pre_state.accounts,
				validator_keys=[],
				authorizer_keys=[],
				privileges=vector.pre_state.privileges
		)

		Accumulation.single_accumulation(
				partial_state,
				work_reports=vector.input.reports,
				services=vector.pre_state.privileges.chi_g,
				service_id=ServiceId(1729),
				timeslot=state.tau
		)