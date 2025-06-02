from jam.state.merkle import StateTrie
from jam.types.state.delta import Delta
from jam.state.ghost import GhostState as State
from tests.dummy.utils import create_dummy_bytes, create_dummy_bytes32


def test_structure():
    state = State.genesis()
    encoded = state.encode()
    decoded_state, _ = State.decode_from(encoded)

    assert state == decoded_state


def test_transform_tree():
    state = State.genesis()
    state.delta = Delta.from_json({
        1: {
            "balance": 0,
            "storage": {
                create_dummy_bytes32(): create_dummy_bytes(10)
            },
            "lookup": {
                create_dummy_bytes32(): create_dummy_bytes(10)
            },
            "timestamps": {
                # create_dummy_bytes32(): []
            },
            "code_hash": create_dummy_bytes32(),
            "gas_limit": 0,
            "min_gas": 0
        },
        2: {
            "balance": 0,
            "storage": {
                create_dummy_bytes32(): create_dummy_bytes(10)
            },
            "lookup": {
                create_dummy_bytes32(): create_dummy_bytes(10)
            },
            "timestamps": {
                # create_dummy_bytes32(): []
            },
            "code_hash": create_dummy_bytes32(),
            "gas_limit": 0,
            "min_gas": 0
        }
    })
    tree = state.transform()

    StateTrie().merkelize(tree)