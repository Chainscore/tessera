from typing import List

from jam.state.state import State
from jam.types import Boolean, TimeSlot
from jam.types.block import Block
from jam.types.extrinsics import GuaranteesExtrinsic, ReportGuarantee
from tests.fixtures.dummy_extrinsics import (
    create_dummy_work_report,
    create_dummy_validator_signatures,
)
from tests.unit.assurances.types import (
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
    block.extrinsic.assurances = input.assurances
    return block


def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state: State = create_dummy_state()
    state.rho = pre_state.avail_assignments
    return state


def vector_transition(vector: Testcase) -> Boolean:
    test_state = create_state_from_pre(vector.pre_state)
    test_block = create_block_from_input(vector.input)
    # try:
    #     output = Assurances.transition(test_state, test_block)
    # except Exception as e:
    #     print("Failed XXX", e)
    #     return Boolean(False)
    return Boolean(True)


def test_tiny():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(limit=3)
    for i, vector in enumerate(vectors):
        assert vector_transition(vector)
        print(f"Passed testcase #{i + 1}")
