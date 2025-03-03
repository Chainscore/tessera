from jam.report.state import Reporting
from jam.state.components.delta import AccountData
from jam.state.state import State
from jam.types import Boolean, Dictionary, ServiceId, Block
from tests.fixtures.dummy_block import create_dummy_block
from tests.fixtures.dummy_state import create_dummy_state
from tests.unit.report.types import Testcase, get_testcases_starting_with, PreState, Input
from typing import List


def create_block_from_input(input:Input) -> Block:

    block = create_dummy_block()
    block.extrinsic.guarantees = input.guarantees
    block.header.slot - input.slot

    return block


def delta_func(pre_state : PreState)-> State.delta:

    account_dict: Dictionary[ServiceId, AccountData]= Dictionary()
    for x in pre_state.accounts:
        account_data = AccountData(storage= Dictionary({}),lookup= Dictionary({}),timestamps= Dictionary({}),code_hash= x.data.service.code_hash, balance= x.data.service.balance , gas_limit= 0, min_gas= x.data.service.min_item_gas)
        account_dict[x.id]= account_data

    return account_dict



def create_state_from_pre(pre_state: PreState) -> State:

    state: State = create_dummy_state()
    state.kappa = pre_state.curr_validators
    state.lambda_ = pre_state.prev_validators
    state.eta = pre_state.entropy
    state.psi.offenders = pre_state.offenders
    state.beta = pre_state.recent_blocks
    state.alpha = pre_state.auth_pools
    state.delta = delta_func(pre_state)

    return  state




def vector_transition(vector:Testcase) -> Boolean:
    test_state = create_state_from_pre(vector.pre_state)
    test_block = create_block_from_input(vector.input)
    hashes = []
    State.alpha
    for x in vector.post_state.avail_assignments:
        hashes.append(x.report.package_spec.hash)

    try:
        output = Reporting.transition(test_state,test_block)
        for x in output.ok.reported:
            if x.work_package_hash == vector.post_state.avail_assignments
            if any(item == x.work_package_hash for item in vector.post_state.avail_assignments[0])
        # if any(x["work_package_hash"] == )



def test_tiny():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(limit=3)
    for i, vector in enumerate(vectors):
        assert vector_transition(vector)
        print(f"Passed testcase #{i + 1}")
