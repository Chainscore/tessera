from typing import List

from jam.consensus.safrole.errors import SafroleError, SafroleErrorCode
from jam.disputes.disputes import Disputes
from jam.state.state import State
from jam.types import Boolean
from jam.types.block import Block
from tests.unit.disputes.types import (
    Input,
    PreState,
    Testcase,
    get_testcases_starting_with,
)
from tests.fixtures.dummy_state import create_dummy_state
from tests.fixtures.dummy_block import create_dummy_block
from jam.disputes.error import DisputesError

def create_block_from_input(input: Input) -> Block:
    """Create a block from test input"""
    block = create_dummy_block()
    block.extrinsic.disputes = input.disputes
    return block


def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state = create_dummy_state()
    # Set psi state components
    state.psi.g = pre_state.psi.good
    state.psi.b = pre_state.psi.bad
    state.psi.w = pre_state.psi.wonky
    state.psi.o = pre_state.psi.offenders
        
    # Set validator sets
    state.kappa = pre_state.kappa
    state.lambda_ = pre_state.lambda_
    
    # Set dispute tracking
    state.rho = pre_state.rho
    state.tau = pre_state.tau
    return state

def vector_transition(vector: Testcase) -> Boolean:
    """
    Test the transition of disputes
    """
    test_state = create_state_from_pre(vector.pre_state)  
    test_block = create_block_from_input(vector.input)
    try:
        try:
            output=Disputes.transition(test_state,test_block)
            for i in vector.output['ok']['offenders_mark']:
                assert str(i) in str(output.psi.o)
            assert output.psi.g == vector.post_state.psi.good
            assert output.psi.b == vector.post_state.psi.bad
            assert output.psi.w == vector.post_state.psi.wonky
            assert output.psi.o == vector.post_state.psi.offenders
            assert output.rho == vector.post_state.rho
            assert output.tau == vector.post_state.tau
            return Boolean(True)
        except DisputesError as e:
            assert e.code._value_==vector.output['err']
            return Boolean(True)
    except:
        return Boolean(False)
        

def test_disputes_transition():
    """Test disputes transition with various test vectors"""
    vectors: List[Testcase] = get_testcases_starting_with(
        limit=100
    )
    for i, vector in enumerate(vectors):
        assert vector_transition(vector)

if __name__ == "__main__":
    test_disputes_transition()





















# def test_disputes_progress(test_file: str):
#     """Test disputes progress with test vectors"""
#     test_data = load_test_data(test_file)
    
#     # Create initial state
#     pre_state = create_state_from_pre(test_data.pre_state)
    
#     # Create block with disputes extrinsic
#     block = create_dummy_block()
#     block.extrinsic.disputes = test_data.input.extrinsic
#     block.header.slot = test_data.input.slot
    
#     # Process disputes
#     result = process_disputes(pre_state, block)
    
#     # Verify output matches expected
#     if test_data.output.ok:
#         assert result.ok
#         assert result.ok.offenders_mark == test_data.output.ok.offenders_mark
#     else:
#         assert result.err == test_data.output.err

