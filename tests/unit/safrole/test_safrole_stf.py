from typing import List

from jam.consensus.safrole.safrole import Safrole
from jam.state.state import State
from jam.types.block import Block
from tests.unit.safrole.types import Input, PreState, Testcase, get_testcases_starting_with
from tests.fixtures.dummy_state import create_dummy_state
from tests.fixtures.dummy_block import create_dummy_block

def create_block_from_input(input: Input) -> Block:
    """Create a block from test input"""
    block = create_dummy_block()
    block.extrinsic.tickets = input.extrinsic
    block.header.slot = input.slot
    block.header.epoch_mark.entropy = input.entropy
    return block

def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state = create_dummy_state()
    state.tau = pre_state.tau
    state.eta = pre_state.eta
    state.lambda_ = pre_state.lambda_
    state.kappa = pre_state.kappa
    state.gamma_k = pre_state.gamma_k
    state.iota = pre_state.iota
    state.gamma_a = pre_state.gamma_a
    state.gamma_s = pre_state.gamma_s
    state.gamma_z = pre_state.gamma_z
    state.post_offenders = pre_state.post_offenders
    return state

def test_publish_tickets_no_mark():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(limit=1, prefix="publish-tickets-no-mark")
    for vector in vectors:
        test_state = create_state_from_pre(vector.pre_state)
        test_block = create_block_from_input(vector.input)
        Safrole.transition(test_state, test_block)