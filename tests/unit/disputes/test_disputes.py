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


def create_block_from_input(input: Input) -> Block:
    """Create a block from test input"""
    block = create_dummy_block()
    block.extrinsic.disputes = input.disputes
    return block




def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state = create_dummy_state()
    # print("state->", pre_state.psi['good'],state.psi.g)
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
    test_state = create_state_from_pre(vector.pre_state)  
    test_block = create_block_from_input(vector.input)
    output=Disputes.transition(test_state,test_block)
    
    # print(output[0].psi.o==vector.post_state.psi.offenders)
    try:
        # if vector.output['ok']:
        #     for i in range(len(vector.output['ok']['offenders_mark'])):
        #         assert str(vector.output['ok']['offenders_mark'][i])==str(output[1]['ok']['offenders_mark'][i])
        # print(" ",output[1],"\n",vector.output)
        if 'err' in vector.output:
            assert output[1]['err'] == vector.output['err']
        elif 'ok' in vector.output:
            for i in range(len(vector.output['ok']['offenders_mark'])):
                assert str(vector.output['ok']['offenders_mark'][i])==str(output[1]['ok']['offenders_mark'][i])
        assert output[0].psi.g == set(vector.post_state.psi.good)
        assert output[0].psi.b == set(vector.post_state.psi.bad)
        assert output[0].psi.w == set(vector.post_state.psi.wonky)
        assert output[0].psi.o == set(vector.post_state.psi.offenders)

        # print("rho->",output[0].rho == vector.post_state.rho)
        # print("tau->",output[0].tau == vector.post_state.tau)
    except Exception as e:
        # print("Error->",e)
        return Boolean(False)
    
    # print("Mine->",output[0].psi.g,vector.post_state.psi['good'])
    # print("Output->",(vector.post_state.psi['good'][0][2:]))

    return Boolean(True)

    # Verify state transitions
    
    
    # Verify output matches expected
    if "err" in vector.output:
        assert output[1]["err"] == vector.output["err"]
    else:
        assert output[1]["ok"] == vector.output["ok"]
        
    return Boolean(True)


def test_disputes_transition():
    """Test disputes transition with various test vectors"""
    vectors: List[Testcase] = get_testcases_starting_with(
        prefix="progress",limit=50
        
    )
    # vector_transition(vectors[4])
    for i, vector in enumerate(vectors):
        # assert vector_transition(vector)
        print(vector_transition(vector))
        # vector_transition(vector)

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

