from copy import deepcopy
from typing import List

from jam.preimages.errors import PreimageError
from jam.preimages.preimages import Preimages
from jam.state.state import State
from jam.types import Boolean, Null, ServiceId
from jam.types.block import Block
from tests.fixtures.dummy_block import create_dummy_block
from tests.fixtures.dummy_state import create_dummy_state
from tests.unit.preimages.types import (
    Input,
    PreState,
    Testcase,
    get_testcases_starting_with,
)

from jam.state.components.delta import LookupTimestamps
from jam.types.protocol.core import BlobLength

def create_block_from_input(input: Input) -> Block:
    """Create a block from test input"""
    block = create_dummy_block()
    block.header.slot = input.slot
    block.extrinsic.preimages = input.preimages
    return block


def create_state_from_pre(pre_state: PreState) -> State:
    """Create a state from pre-state"""
    state: State = create_dummy_state()
    for account in pre_state.accounts:
        if account.id not in state.delta:
            state.delta[account.id] = deepcopy(state.delta[ServiceId(0)])
        for preimage in account.data.preimages:
            state.delta[account.id].lookup[preimage.hash] = preimage.blob
        for lookup in account.data.lookup_meta:
            state.delta[account.id].timestamps[LookupTimestamps.get_key(lookup.key.hash,BlobLength(lookup.key.length))] = lookup.value
    return state


def vector_transition(vector: Testcase) -> Boolean:
    test_state = create_state_from_pre(vector.pre_state)
    test_block = create_block_from_input(vector.input)

    try:
        output_state = Preimages.transition(test_state, test_block)
        if vector.output.get_value() != Null:
            raise Exception("Expected ERROR output but got Null")

        expected_state = create_state_from_pre(vector.post_state)
        assert output_state == expected_state
    except PreimageError as e:
        assert vector.output.get_value() == e.code
    return Boolean(True)


def test_tiny():
    """Test publishing tickets with no mark"""
    vectors: List[Testcase] = get_testcases_starting_with(limit=8)
    for i, vector in enumerate(vectors):
        assert vector_transition(vector)
        print(f"✅Passed testcase #{i + 1}")
