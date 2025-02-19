from typing import List

from jam.consensus.safrole.errors import SafroleError, SafroleErrorCode
from jam.consensus.safrole.safrole import Safrole
from jam.state.state import State
from jam.types import Boolean
from jam.types.block import Block
from tests.unit.safrole.types import (
    Input,
    PreState,
    Testcase,
    get_testcases_starting_with,
)
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
    state: State = create_dummy_state()
    state.tau = pre_state.tau
    state.lambda_ = pre_state.lambda_
    state.kappa = pre_state.kappa
    state.psi.g = pre_state.good
    state.psi.b = pre_state.bad
    state.psi.w = pre_state.wonky
    state.psi.o = pre_state.offenders
    state.rho = pre_state.rho
    return state

def vector_transition(vector: Testcase) -> Boolean:
    test_state = create_state_from_pre(vector.pre_state)
    test_block = create_block_from_input(vector.input)
    try:
        output = Safrole.transition(test_state, test_block)
        assert output.tau == vector.post_state.tau
        # assert output.eta[0] == vector.post_state.eta[0]
        assert output.eta[1] == vector.post_state.eta[1]
        assert output.eta[2] == vector.post_state.eta[2]
        assert output.eta[3] == vector.post_state.eta[3]
        assert output.lambda_ == vector.post_state.lambda_
        assert output.kappa == vector.post_state.kappa
        assert output.gamma.k == vector.post_state.gamma_k
        assert output.iota == vector.post_state.iota
        assert output.gamma.a == vector.post_state.gamma_a
        assert output.gamma.s == vector.post_state.gamma_s.value
        # assert output.gamma.z == vector.post_state.gamma_z
        assert output.psi.o == vector.post_state.post_offenders
    except SafroleError as e:
        # TODO: remove this once vrf module is implemented
        if e.code == SafroleErrorCode.BAD_TICKET_PROOF:
            pass
        else:
            assert e.code == vector.output.value
    return Boolean(True)


def test_disputes_transition():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(
        limit=0, prefix="progress_with_no_verdicts"
    )
    for i, vector in enumerate(vectors):
        assert vector_transition(vector)
        print(f"Passed testcase #{i + 1}")

test_disputes_transition()


# def test_publish_tickets_no_mark():
#     """Test publishing tickets with no mark"""
#     vectors: List[Testcase] = get_testcases_starting_with(
#         limit=0, prefix="publish-tickets-no-mark"
#     )
#     for i, vector in enumerate(vectors):
#         assert vector_transition(vector)
#         print(f"Passed testcase #{i + 1}")
