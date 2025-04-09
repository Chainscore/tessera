from typing import List

from jam.state.state import State
from jam.types import Boolean
from jam.types.block import Block
from tests.unit.assurances.types import (
    Input,
    PreState,
    Testcase,
    get_testcases_starting_with,
)
from tests.fixtures.dummy_state import create_dummy_state
from tests.fixtures.dummy_block import create_dummy_block
from jam.assurances.assurances import Assurances
from jam.assurances.errors import AssurancesError

def create_block_from_input(input: Input) -> Block:
    """Create a block from test input"""
    block = create_dummy_block()
    block.extrinsic.assurances = input.assurances
    block.header.parent = input.parent
    block.header.slot = input.slot
    return block


def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state: State = create_dummy_state()
    state.rho = pre_state.avail_assignments
    state.kappa = pre_state.curr_validators
    return state

def vector_transition(vector: Testcase) -> Boolean:

    test_state = create_state_from_pre(vector.pre_state)
    test_block = create_block_from_input(vector.input)
    try:
        output, available_wrs = Assurances.transition(test_state, test_block)
        assert output == create_state_from_pre(vector.post_state)
    except AssurancesError as e:
        assert e.code == vector.output.get_value()
    except Exception as e:
        print("Failed", e)
        assert False

def test_assurance_for_not_engaged_core():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(prefix="assurance_for_not_engaged_core")
    for i, vector in enumerate(vectors):
        vector_transition(vector)

def test_assurance_with_bad_attestation_parent():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(prefix="assurance_with_bad_attestation_parent")
    for i, vector in enumerate(vectors):
        vector_transition(vector)

def test_assurances_for_stale_report():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(prefix="assurances_for_stale_report")
    for i, vector in enumerate(vectors):
        vector_transition(vector)


def test_no_assurances_with_stale_report():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(prefix="no_assurances_with_stale_report")
    for i, vector in enumerate(vectors):
        vector_transition(vector)

def test_assurances_with_bad_validator_index():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(prefix="assurances_with_bad_validator_index")
    for i, vector in enumerate(vectors):
        vector_transition(vector)

def test_assurers_not_sorted_or_unique():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(prefix="assurers_not_sorted_or_unique")
    for i, vector in enumerate(vectors):
        vector_transition(vector)

def test_some_assurances():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(prefix="some_assurances")
    for i, vector in enumerate(vectors):
        vector_transition(vector)
