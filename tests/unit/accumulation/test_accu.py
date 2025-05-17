import json
from pathlib import Path

import pytest

from jam.types.state.sigma import Sigma
from jam.types.block import Block
from jam.types.header import Header
from jam.types.extrinsics.extrinsic import Extrinsic
from jam.state.accounts import AccountMetadata
from jam.types.state.delta import ServiceCodeHash, Ao, Ai, LookupTable, Timestamps
from jam.types.protocol.core import Balance, Gas, ServiceId


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

    # state.eta[0]=vector.pre_state.entropy
    # state.chi = vector.pre_state.privileges

    for wr_index in range(0,len(vector.pre_state.ready_queue)):
        state.nu[wr_index]=vector.pre_state.ready_queue[wr_index]


    state.xi=vector.pre_state.accumulated
    state.pi.services=vector.pre_state.statistics
    state.tau=vector.pre_state.slot

    print(state.nu)
    # print("prestate",type(vector.pre_state.ready_queue[0]))

    for key in vector.pre_state.accounts:
        account_metadata = AccountMetadata(
            code_hash=ServiceCodeHash(vector.pre_state.accounts[key].service.code_hash),
            balance=Balance(vector.pre_state.accounts[key].service.balance),
            gas_limit=Gas(vector.pre_state.accounts[key].service.min_item_gas),
            min_gas=Gas(vector.pre_state.accounts[key].service.min_memo_gas),
            num_o=Ao(vector.pre_state.accounts[key].service.bytes),
            num_i=Ai(vector.pre_state.accounts[key].service.items)
        )
        state.delta[key]=account_metadata

    block = Block(header=Header.genesis(path="genesis.json"), extrinsic=Extrinsic.empty())
    block.header.slot = vector.input.slot
    block.extrinsic.guarantees = vector.input.reports
    # print(vector.pre_state.accounts[key])
    # print(state.delta[1729])
    post_state=Accumulation.transition(pre_state=state, block=block)
    # print(post_state.tau)
    # print(post_state.chi)
    # print(post_state.nu)
    # print(post_state.xi)
    # print(post_state.eta[0])
