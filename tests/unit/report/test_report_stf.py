from jam.report.error import ReportingError, ReportingErrorCode
from jam.report.state import Reporting
from jam.state.components.beta import PackageDict, Beta
from jam.state.components.delta import AccountData
from jam.state.state import State
from jam.types import Boolean, Dictionary, ServiceId, Block
from tests.fixtures.dummy_block import create_dummy_block
from tests.fixtures.dummy_state import create_dummy_state
from tests.unit.report.types import Testcase, get_testcases_starting_with, PreState, Input
from typing import List
from jam.types.protocol.core import (
    SegmentRoot,
    WorkPackageHash,
)

def create_block_from_input(input:Input) -> Block:

    block = create_dummy_block()
    block.extrinsic.guarantees = input.guarantees
    block.header.slot = input.slot

    return block


def delta_func(pre_state : PreState)-> Dictionary():

    account_dict: Dictionary[ServiceId, AccountData]= Dictionary()
    for x in pre_state.accounts:
        account_data = AccountData(storage= Dictionary({}),lookup= Dictionary({}),timestamps= Dictionary({}),code_hash= x.data.service.code_hash, balance= x.data.service.balance , gas_limit= 0, min_gas= x.data.service.min_item_gas)
        account_dict[x.id]= account_data

    return account_dict


def create_state_from_pre(pre_state: PreState) -> State:

    state: State = create_dummy_state()
    state.rho = pre_state.avail_assignments
    state.kappa = pre_state.curr_validators
    state.lambda_ = pre_state.prev_validators
    state.eta = pre_state.entropy
    state.psi.offenders = pre_state.offenders
    state.beta = pre_state.recent_blocks.to_beta()
    # print('',state.beta)
    # print('d1',pre_state.auth_pools)
    state.alpha = pre_state.auth_pools
    # print('d2',state.alpha)
    state.delta = delta_func(pre_state)

    return  state




def vector_transition(vector:Testcase) -> Boolean:
    test_state = create_state_from_pre(vector.pre_state)
    # print('pre_state', test_state)
    test_block = create_block_from_input(vector.input)
    # print('block',test_block)
    # hashes = []
    # State.alpha
    # for x in vector.post_state.avail_assignments:
    #     hashes.append(x.report.package_spec.hash)

    post_state = create_state_from_pre(vector.post_state)
    # output = Reporting.transition(test_state,test_block)
    # print('output.rho',output)
    # print('ouuuuuttt',vector.output['err'])
    try:
        output = Reporting.transition(test_state, test_block)
        # print('State transition')
        assert output == create_state_from_pre(vector.post_state)
        avail_assignments_report = []
        avail_assignments_slot = []
        rho_report = []
        rho_timeout = []
        # print(output.rho)
        # print('xxxxxxxxxx',output.rho[0].get_value().report == output.rho[1].get_value().report)
        # print('xxxxx2',vector.post_state.avail_assignments[1].get_value().report)
        # for x in range (len(vector.post_state.avail_assignments)):
        #     avail_assignments_report.append(vector.post_state.avail_assignments[x].get_value().report)
        #     rho_report.append(output.rho[x].get_value().report)
        #     avail_assignments_slot.append(vector.post_state.avail_assignments[x].get_value().timeout)
        #     rho_timeout.append(output.rho[x].get_value().timeout)
            # assert vector.post_state.avail_assignments[x].get_value().report == output.rho[x].get_value().report)
        # print(rho_timeout,avail_assignments_slot,avail_assignments_report==rho_report)
        # assert vector.post_state.avail_assignments[0].get_value().report == output.rho[0].get_value().report
        # assert avail_assignments_slot == rho_timeout
        # assert output == vector.post_state
        # print('hiii')
        return True

    except ReportingError as e:
        if e.code._value_ == ReportingErrorCode.BAD_BEEFY_MMR_ROOT:
            pass
        # print('eeeeeerrrrr',e.code._value_)
        assert e.code._value_ == vector.output['err']

    # assert output == post_state
        # for x in output.ok.reported:
        #     if x.work_package_hash == vector.post_state.avail_assignments
        #     if any(item == x.work_package_hash for item in vector.post_state.avail_assignments[0])
        # # if any(x["work_package_hash"] ==
        return Boolean(True)



def test_tiny():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(limit=38)
    for i, vector in enumerate(vectors):
        assert vector_transition(vector)
        print(f"Passed testcase #{i + 1}")
