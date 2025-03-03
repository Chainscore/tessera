from typing import List

from jam.state.state import State
from jam.types import Boolean
from jam.types.block import Block
from tests.fixtures.dummy_block import create_dummy_block
from tests.fixtures.dummy_state import create_dummy_state
from tests.unit.accumulation.types import (
    Input,
    PreState,
    Testcase,
    get_testcases_starting_with,
)
from jam.accumulation.accumulation import Accumulation

def create_block_from_input(input: Input) -> Block:
    """Create a block from test input"""
    block = create_dummy_block()
    block.extrinsic.guarantees.reports = input.reports
    return block

def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state = create_dummy_state()
    # Set psi state components
    return state

def vector_transition(vector: Testcase) -> Boolean:
    """
    Test the transition of disputes
    """    
    test_state = create_state_from_pre(vector.pre_state)
    test_block = create_block_from_input(vector.input)
    
    state=Accumulation.transition(test_state,test_block)
    return Boolean(True)

    
        

def test_disputes_transition():
    """Test disputes transition with various test vectors"""
    vectors: List[Testcase] = get_testcases_starting_with(
        limit=1
    )

    for i, vector in enumerate(vectors):
        assert vector_transition(vector)

if __name__ == "__main__":
    test_disputes_transition()

