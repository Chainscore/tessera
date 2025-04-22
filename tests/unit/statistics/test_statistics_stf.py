from typing import List

from jam.state.components.pi import AllServiceStats, Pi
from jam.state.state import State
from jam.statistics.statistics import Statistics
from jam.types import Boolean
from jam.types.block import Block
from tests.fixtures.dummy_block import create_dummy_block
from tests.fixtures.dummy_state import create_dummy_state
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


def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state: State = create_dummy_state()
    all_service_stats = AllServiceStats()
    for service_record in pre_state.statistics.services:
        all_service_stats[service_record.id] = service_record.record

    Py = Pi(
        vals_current=pre_state.statistics.vals_current,
        vals_last=pre_state.statistics.vals_last,
        cores=pre_state.statistics.cores,
        services=all_service_stats,
    )

    state.pi = Py
    state.tau = pre_state.slot
    return state


def vector_transition(vector: Testcase) -> Boolean:
    test_block = create_block_from_input(vector.input)
    test_state = create_state_from_pre(vector.pre_state)
    expected_state = create_state_from_pre(vector.post_state)

    try:
        output_state = Statistics.transition(test_state, test_block, [], {}, {})
        # return Boolean(True)
        assert output_state.pi.vals_current == expected_state.pi.vals_current
        assert output_state.pi.vals_last == expected_state.pi.vals_last
        assert output_state.pi.cores == expected_state.pi.cores
        assert output_state.pi.services == expected_state.pi.services
        # assert output.pi.vals_last == vector.post_state.pi.last
    except Exception as e:
        print("Failed XXX", e)
        return Boolean(False)
    return Boolean(True)


def test_tiny():
    """Test statistics transition"""
    vectors: List[Testcase] = get_testcases_starting_with(limit=3)
    for i, vector in enumerate(vectors):
        assert vector_transition(vector)
        print(f"Passed testcase #{i + 1}")
