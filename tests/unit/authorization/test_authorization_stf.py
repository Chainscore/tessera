from typing import List

from jam.authorization.authorization import Authorization
from jam.state.state import State
from jam.types import Boolean, TimeSlot
from jam.types.block import Block
from jam.types.extrinsics import GuaranteesExtrinsic, ReportGuarantee
from tests.fixtures.dummy_extrinsics import (
    create_dummy_work_report,
    create_dummy_validator_signatures,
)
from tests.unit.authorization.types import (
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
    block.header.slot = input.slot
    block.extrinsic.guarantees = GuaranteesExtrinsic(
        [
            ReportGuarantee(
                report=create_dummy_work_report(),
                slot=TimeSlot(42),
                signatures=create_dummy_validator_signatures(),
            )
            for _ in input.auths
        ]
    )
    for i, auth in enumerate(input.auths):
        block.extrinsic.guarantees[i].report.core_index = auth.core
        block.extrinsic.guarantees[i].report.authorizer_hash = auth.auth_hash

    return block


def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state: State = create_dummy_state()
    state.alpha = pre_state.auth_pools
    state.phi = pre_state.auth_queues
    return state


def vector_transition(vector: Testcase) -> Boolean:
    test_state = create_state_from_pre(vector.pre_state)
    test_block = create_block_from_input(vector.input)
    try:
        output = Authorization.transition(test_state, test_block)
        assert output.alpha == vector.post_state.auth_pools
        assert output.phi == vector.post_state.auth_queues
    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)


def test_tiny():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(limit=3)
    for i, vector in enumerate(vectors):
        assert vector_transition(vector)
        print(f"Passed testcase #{i + 1}")


# if __name__ == "__main__":
#     test_tiny()