from typing import List

from jam.state.components.chi import ChiG
# from jam.consensus.safrole.errors import SafroleError, SafroleErrorCode
# from jam.disputes.disputes import Disputes
from jam.state.state import State
from jam.types import Boolean
from jam.types.block import Block
from jam.types.extrinsics import GuaranteesExtrinsic
from tests.fixtures.dummy_block import create_dummy_block
from tests.fixtures.dummy_state import create_dummy_state
from tests.unit.accumulation.types import (
    Input,
    PreState,
    Testcase,
    get_testcases_starting_with, InputPreimages,
)

from jam.accumulation.accumulation import Accumulation
from jam.state.components.delta import Delta, AccountData, AccountStorage, PreImageLookup, LookupTimestamps
from jam.state.components.nu import Nu
from jam.state.components.xi import Xi
from jam.types.extrinsics.guarantees import ReportGuarantee
from tests.fixtures.dummy_extrinsics import create_dummy_validator_signatures


def create_block_from_input(test_input: Input) -> Block:
    """Create a block from test input"""
    block = create_dummy_block()
    block.extrinsic.guarantees = GuaranteesExtrinsic([])
    for i in test_input.reports:
        block.extrinsic.guarantees.append(ReportGuarantee(report=i,slot=test_input.slot,signatures=create_dummy_validator_signatures()))
    block.header.slot = test_input.slot
    return block

def package_preimages(preimages: InputPreimages) -> PreImageLookup:
    lookup = PreImageLookup({})

    for pi in preimages:
        lookup[pi.hash] = pi.blob
    return lookup

def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state = create_dummy_state()
    state.tau = pre_state.slot
    state.nu = pre_state.ready_queue
    state.xi = pre_state.accumulated
    state.eta[0] = pre_state.entropy

    # Not sure about altering first element of eta

    state.chi.m=pre_state.privileges.bless
    state.chi.a=pre_state.privileges.assign
    state.chi.v=pre_state.privileges.designate

    # Convert Privileges into ChiG
    state.chi.g = ChiG({})
    for index, acc in enumerate(pre_state.privileges.always_acc):
        state.chi.g[acc.service_id] = pre_state.privileges.always_acc[index].gas

    # Set Delta props
    state.delta = Delta({})
    for i in pre_state.accounts:
        state.delta[i.id] = AccountData(
            storage=AccountStorage({}),
            lookup=package_preimages(i.data.preimages),
            timestamps=LookupTimestamps({}),
            code_hash=i.data.service.code_hash,
            balance=i.data.service.balance,
            gas_limit=i.data.service.min_item_gas,
            min_gas=i.data.service.min_memo_gas
        )
    
    return state

def vector_transition(vector: Testcase) -> Boolean:
    """
    Test the transition of accumulation module
    """    
    test_block = create_block_from_input(vector.input)
    test_state = create_state_from_pre(vector.pre_state)

    op_state = create_state_from_pre(vector.post_state)
    state=Accumulation.transition(test_state,test_block)

    # ξ′
    assert op_state.xi == state.xi

    # ϑ`
    assert op_state.nu == state.nu

    # δ‡
    assert op_state.delta == state.delta

    # χ′
    assert op_state.chi == state.chi

    # ι′
    assert op_state.iota == state.iota

    # φ′
    assert op_state.phi == state.phi

    return Boolean(True)

        

def test_accumulation_transition():
    """Test accumulation transition with various test vectors"""
    vectors: List[Testcase] = get_testcases_starting_with(
        "enqueue_and_unlock_chain-1",limit=1
        # "",limit=20
    )
    for i, vector in enumerate(vectors):
        assert vector_transition(vector)
        print("passed testcase", i+1)

if __name__ == "__main__":
    test_accumulation_transition()

