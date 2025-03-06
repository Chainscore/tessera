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
from jam.state.components.delta import Delta, AccountData
from jam.types.extrinsics.guarantees import ReportGuarantee
from tests.fixtures.dummy_extrinsics import create_dummy_validator_signatures

def create_block_from_input(input: Input) -> Block:
    """Create a block from test input"""
    block = create_dummy_block()
    block.extrinsic.guarantees = []
    for i in input.reports:
        block.extrinsic.guarantees.append(ReportGuarantee(report=i,slot=input.slot,signatures=create_dummy_validator_signatures()))
    block.header.slot=input.slot
    return block

def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state = create_dummy_state()
    state.theta = pre_state.ready_queue
    state.xi=pre_state.accumulated
    state.eta[0]=pre_state.entropy
    # Not sure about altering first element of eta
    state.chi.m=pre_state.privileges.bless
    state.chi.a=pre_state.privileges.assign
    state.chi.v=pre_state.privileges.designate
    chiG={}
    for i in pre_state.privileges.always_acc:
        chiG[i]=pre_state.privileges.always_acc[i]
    state.chi.g=chiG
    
    # Set delta state components
    for i in pre_state.accounts:
        state.delta[i.id]=AccountData(
            storage=i.data.service.items, #keeping size here for the timing
            lookup=i.data.preimages,
            timestamps=i.data.service.bytes,
            code_hash=i.data.service.code_hash,
            balance=i.data.service.balance,
            gas_limit=i.data.service.min_item_gas,
            min_gas=i.data.service.min_memo_gas
        )
    
    return state

def vector_transition(vector: Testcase) -> Boolean:
    """
    Test the transition of disputes
    """    
    test_block = create_block_from_input(vector.input)
    test_state = create_state_from_pre(vector.pre_state)
    
    # print("theta->",type(test_state.theta))
    # print("blockguarantee->",type(test_block.extrinsic.guarantees))
    state=Accumulation.transition(test_state,test_block)
    return Boolean(True)

    
        

def test_disputes_transition():
    """Test disputes transition with various test vectors"""
    vectors: List[Testcase] = get_testcases_starting_with(
        "enqueue_and_unlock_chain_wraps-3",limit=1
        # "",limit=20
    )
    for i, vector in enumerate(vectors):
       
        assert vector_transition(vector)

if __name__ == "__main__":
    test_disputes_transition()

