# tests/unit/psiA/test_psiA.py
import json
from pathlib import Path

import pytest

from tests.unit.psiA.type_psiA import TestcasePsiA
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
def test_PsiA_host_call(vector: TestcasePsiA):
    # vector.input  → your Input
    # vector.pre_state → your PreState
    # vector.output → expected Output
    # vector.post_state → expected PostState
    print(vector.input)
    # 1) invoke your host‐call
    # actual_output, actual_post_state = PsiA(vector.input, vector.pre_state)

    # 2) compare against expected
    # assert actual_output == vector.output
    # assert actual_post_state == vector.post_state
