from jam.state.components.delta import Delta
from jam.state.state import State
from jam.types.protocol.crypto import BandersnatchPublic, Ed25519Public, BlsPublic
from jam.types.protocol.validators import ValidatorData, ValidatorMetadata
from jam.utils.constants import VALIDATOR_COUNT
from tests.fixtures.utils import create_dummy_bytes, create_dummy_bytes32
from jam.consensus.safrole.safrole import Safrole
from jam.types.base.sequences.bytes.byte_array import ByteArray32


def test_structure():
    dummy_vals = [ValidatorData(
        bandersnatch=BandersnatchPublic(create_dummy_bytes32()),
        ed25519=Ed25519Public(create_dummy_bytes32()),
        bls=BlsPublic(create_dummy_bytes(144)),
        metadata=ValidatorMetadata(create_dummy_bytes(128)),
    )
        for _ in range(VALIDATOR_COUNT)
    ]
    state = State.genesis(dummy_vals, Safrole.arrange_fallback(
        ByteArray32(bytes(32)), dummy_vals))
    encoded = state.encode()
    decoded_state, _ = State.decode_from(encoded)

    assert state == decoded_state


def test_transform_tree():
    dummy_vals = [ValidatorData(
        bandersnatch=BandersnatchPublic(create_dummy_bytes32()),
        ed25519=Ed25519Public(create_dummy_bytes32()),
        bls=BlsPublic(create_dummy_bytes(144)),
        metadata=ValidatorMetadata(create_dummy_bytes(128)),
    )
        for _ in range(VALIDATOR_COUNT)
    ]
    state = State.genesis(dummy_vals, Safrole.arrange_fallback(
        ByteArray32(bytes(32)), dummy_vals))
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

    state._merkle.merkelize(tree)
    print("Tree:\n")
    for i in sorted(tree.items()):
        print([int(val) for val in state._merkle.bits(i[0])])
        print("\n")

    print(bin(160)[2:])
