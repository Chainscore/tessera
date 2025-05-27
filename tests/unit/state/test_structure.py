from jam.state.merkle import StateTrie
from jam.types.state.delta import Delta
from jam.state.ghost import GhostState as State
from jam.utils.dummy.utils import create_dummy_bytes, create_dummy_bytes32


def test_structure():
    state = State.genesis()
    encoded = state.encode()
    decoded_state, _ = State.decode_from(encoded)
    assert state == decoded_state


def test_transform_tree():
    state = State.genesis()
    state.delta = Delta.from_json({
        1: {
            "service": {
                "code_hash": create_dummy_bytes32(),
                "min_memo_gas": 0,
                "min_item_gas": 0,
                "balance": 0,
                "items": 0,
                "bytes": 0
            },
            "storage": [
                {
                    "key": create_dummy_bytes32(),
                    "value": create_dummy_bytes(10)
                }
            ],
            "preimages": [
                {
                    "hash": create_dummy_bytes32(),
                    "blob": create_dummy_bytes(10)
                }
            ],
            "lookup_meta": [
                # create_dummy_bytes32(): []
            ],
        },
        # Dict accepts either a list or dict
        2: {
            "service": {
                "code_hash": create_dummy_bytes32(),
                "min_memo_gas": 0,
                "min_item_gas": 0,
                "balance": 0,
                "items": 0,
                "bytes": 0
            },
            "storage": {
                    create_dummy_bytes32(): create_dummy_bytes(10)
            },
            "preimages": {
                    create_dummy_bytes32(): create_dummy_bytes(10)
            },
            "lookup_meta": {
                # create_dummy_bytes32(): []
            },
        }
    })
    tree = state.transform()

    StateTrie().merkelize(tree)