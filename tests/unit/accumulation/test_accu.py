import json
from pathlib import Path

import pytest

from jam.types.state.sigma import Sigma
from jam.types.block import Block
from jam.types.header import Header
from jam.types.extrinsics.extrinsic import Extrinsic

from jam.accumulation.accumulation import Accumulation
from jam.config.data_stores import main_db
from jam.state.ghost import GhostState
from jam.state.state import setup_state
from jam.types.protocol.core import ServiceId
from jam.types.work.report import WorkReport, WorkReports
from tests.unit.accumulation.types import AccuTestCase, StateContext, OperandTuple, OperandTuples

# directory where your tiny test vectors live
TEST_DATA_DIR = Path(__file__).parent / "tiny"


def load_test_vectors():
    """
    Yield one AccuTestCase for each JSON file matching the
    '*.json' pattern in the tiny/ directory.
    """
    for json_path in TEST_DATA_DIR.glob("*.json"):
        try:
            # Print the filename to check which file is being loaded
            print(f"Loading test case from file: {json_path.name}")
            data = json.loads(json_path.read_text())
            yield AccuTestCase.from_json(data)
            break
        except Exception as e:
            # Print the error message along with the filename if there is an issue
            print(f"Error occurred while loading {json_path.name}: {e}")


@pytest.mark.parametrize("vector", load_test_vectors(), ids=lambda v: v.input.slot)
def test_accumulation(vector: AccuTestCase):
    setup_state(GhostState.genesis(), main_db)
    from jam.state.state import state
    # for service_id, data in vector.pre_state.accounts.items():
    #     state.delta[service_id] = data
    state.chi = vector.pre_state.privileges
    # partial_state = StateContext(
    #     service_accounts=vector.pre_state.accounts,
    #     validator_keys=[],
    #     authorizer_keys=[],
    #     privileges=state.chi
    # )
    pre_state = Sigma(
        alpha=state.alpha,
        beta=state.beta,
        gamma=state.gamma,
        delta=vector.pre_state.accounts,
        eta=state.eta,
        iota=state.iota,
        kappa=state.iota,
        lambda_=state.lambda_,
        rho=state.rho,
        tau=vector.pre_state.slot,
        phi=state.phi,
        chi=vector.pre_state.privileges,
        psi=state.psi,
        pi=state.pi,
        nu=vector.pre_state.ready_queue,
        xi=vector.pre_state.accumulated
    )
    pre_state.pi.services = vector.pre_state.statistics

    block = Block(header=Header.genesis(path="genesis.json"), extrinsic=Extrinsic.empty())
    block.header.slot = vector.input.slot
    block.extrinsic.guarantees = vector.input.reports
    print(state.delta)
    # Accumulation.transition(pre_state=pre_state, block=block)
