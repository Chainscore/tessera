# tests/unit/psiA/test_psiA.py
import json
from pathlib import Path

import pytest

from jam.accumulation.accumulation import Accumulation
from jam.config.data_stores import main_db
from jam.state.ghost import GhostState
from jam.state.state import setup_state
from jam.types.protocol.core import ServiceId
from jam.types.work.report import WorkReport, WorkReports
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
		setup_state(GhostState.genesis(), main_db)
		from jam.state.state import state

		partial_state = StateContext(
				service_accounts=vector.pre_state.accounts,
				validator_keys=[],
				authorizer_keys=[],
				privileges=vector.pre_state.privileges
		)

		Accumulation.single_accumulation(
				partial_state,
				work_reports=WorkReports([WorkReport.from_json({
            "package_spec": {
              "hash": "0x36a748779db31316ac26eebc08dadbeda8a8d4794892f6e340e32ab69e0d4d80",
              "length": 9,
              "erasure_root": "0x9cc608578f92d440e1c11dbcc5af07ee25aba742f8788317108ba3dce2f26543",
              "exports_root": "0xf50c02f87ec50cec00c10eeefe071eeb7e623446e7030add118c6c592618b165",
              "exports_count": 7
            },
            "context": {
              "anchor": "0x926e15a4c487b4571bef5dc98498a1b1ce7472862945984013e46d003e15de3b",
              "state_root": "0x8258273eed954fe03da306e2bac3bde66250fe3dac8d8471e94d8c2fb9595022",
              "beefy_root": "0x8d6899f7eb78610fa3a40a011a325582369e20c87de707567f93d6a0a3ecb5d7",
              "lookup_anchor": "0x4cbb258e187f5ecb7ccdcb5f15c44e3163b55e4e4eb5f2af99358b202b9db31c",
              "lookup_anchor_slot": 40,
              "prerequisites": [
                "0xd3d0ac423a2e9451db2e88bd75cc143b19424747fbcf2696792987436e8722a6"
              ]
            },
            "core_index": 0,
            "authorizer_hash": "0xfdfe51dc958e91de500cec6d90503e0f898cfdbbc95a9345277f9368ea4b4aee",
            "auth_output": "0x",
            "segment_root_lookup": [],
            "results": [
              {
                "service_id": 1729,
                "code_hash": "0x310b17cf654f7de806b4f6da081ad39cb1d5ba7e82cb51a8014f70b20dc86658",
                "payload_hash": "0xeb2579a6a43ec9cf3ef30059f68ba4691c2c996e32411f35bc8630f89dfa5b86",
                "accumulate_gas": 10000,
                "result": {
                  "ok": "0x64756d6d79"
                },
                "refine_load": {
                  "gas_used": 0,
                  "imports": 0,
                  "extrinsic_count": 0,
                  "extrinsic_size": 0,
                  "exports": 0
                }
              }
            ],
            "auth_gas_used": 0
          })]),
				services=vector.pre_state.privileges.chi_g,
				service_id=ServiceId(1729),
				timeslot=state.tau
		)