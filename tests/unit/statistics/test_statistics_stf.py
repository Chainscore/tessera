from typing import List

from jam.state.components.pi import AllValidatorStats, Pi, ValidatorStat
from jam.state.state import State
from jam.statistics.statistics import Statistics
from jam.types import Boolean
from jam.types.block import Block
from tests.fixtures.dummy_block import create_dummy_block
from tests.fixtures.dummy_state import create_dummy_state
from tests.unit.statistics.types import AllValidatorStats as TestValidatorStats
from tests.unit.statistics.types import (
    Input,
    PreState,
    Testcase,
    get_testcases_starting_with,
)


def create_block_from_input(input: Input) -> Block:
    """Create a block from test input"""
    block = create_dummy_block()
    block.header.slot = input.slot
    block.header.author_index = input.author_index

    block.extrinsic = input.extrinsic

    return block


def transform_test_to_base(stats: TestValidatorStats) -> AllValidatorStats:
    validator_stats = []
    for validator in stats:
        validator_stat = ValidatorStat(
            blocks=validator.blocks,
            tickets=validator.tickets,
            pre_images=validator.pre_images,
            pre_images_size=validator.pre_images_size,
            guarantees=validator.guarantees,
            assurances=validator.assurances,
        )
        validator_stats.append(validator_stat)

    return AllValidatorStats(validator_stats)


def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state: State = create_dummy_state()
    Py = Pi(
        [
            transform_test_to_base(pre_state.pi.current),
            transform_test_to_base(pre_state.pi.last),
        ]
    )
    state.pi = Py
    state.tau = pre_state.tau
    return state


def vector_transition(vector: Testcase) -> Boolean:
    test_block = create_block_from_input(vector.input)
    test_state = create_state_from_pre(vector.pre_state)
    try:
        output = Statistics.transition(test_state, test_block)
        assert output.pi[0] == transform_test_to_base(vector.post_state.pi.current)
        assert output.pi[1] == transform_test_to_base(vector.post_state.pi.last)
        # assert output.pi[0] == AllValidatorStats(vector.post_state.pi.current)
        # assert output.pi[1] == AllValidatorStats(vector.post_state.pi.last)
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
