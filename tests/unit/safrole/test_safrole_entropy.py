from copy import deepcopy

import pytest
from tsrkit_types.bytes import Bytes

from jam.state.transitions import Safrole
from jam.types.state.eta import Eta
from tsrkit_types.integers import U32
from jam.types.state.kappa import Kappa
from jam.types.state.gamma import GammaK, GammaA, GammaS, GammaSFallback, GammaZ
from jam.types.state.psi import PsiO
from jam.types.state.iota import Iota
from jam.types.state.lambda_ import Lambda_
from jam.types.protocol.crypto import Hash
from tests.unit.safrole.data import create_block, create_state, create_validator_data_from_keys
from jam.utils.constants import EPOCH_LENGTH


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_entropy_accumulation():
    """Test that Safrole correctly accumulates entropy"""
    # Create initial state with known entropy values
    test_entropy = [Bytes[32](bytes([i + 1] * 32)) for i in range(4)]
    eta = Eta(test_entropy)
    initial_state = create_state(
        tau=U32(5),
        eta=eta,
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_k=GammaK(create_validator_data_from_keys()),
        iota=Iota(create_validator_data_from_keys()),
        gamma_a=GammaA([]),
        gamma_s=GammaS(
            GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2])
        ),
        gamma_z=GammaZ(
            Safrole.compute_ring_root(
                [keys.bandersnatch for keys in create_validator_data_from_keys()]
            )
        ),
        offenders=PsiO([]),
    )

    # Create a block with block entropy
    block_entropy = Bytes[32](bytes([42] * 32))
    new_block = create_block(slot=U32(6), tickets=[])

    # Apply the transition
    new_state = Safrole.transition(deepcopy(initial_state), new_block, block_entropy)

    # Check that the entropy was accumulated η'₀ = H(η₀ || VRF_output(H_v))
    expected_new_entropy = Hash.blake2b(bytes(initial_state.eta[0]) + bytes(block_entropy))
    assert new_state.eta[0] == Bytes[32](
        expected_new_entropy
    ), "Entropy should be updated correctly"

    # Other entropy slots should remain unchanged
    assert new_state.eta[1] == initial_state.eta[1]
    assert new_state.eta[2] == initial_state.eta[2]
    assert new_state.eta[3] == initial_state.eta[3]


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_entropy_rotation_at_epoch_boundary():
    """Test that Safrole correctly rotates entropy values at epoch boundaries"""
    # Create initial state at the last slot of an epoch with known entropy values
    test_entropy = [
        Bytes[32](bytes([1] * 32)),  # η₀
        Bytes[32](bytes([2] * 32)),  # η₁
        Bytes[32](bytes([3] * 32)),  # η₂
        Bytes[32](bytes([4] * 32)),  # η₃
    ]
    eta = Eta(test_entropy)

    last_slot_in_epoch = U32(EPOCH_LENGTH - 1)
    initial_state = create_state(
        tau=last_slot_in_epoch,
        eta=eta,
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_k=GammaK(create_validator_data_from_keys()),
        iota=Iota(create_validator_data_from_keys()),
        gamma_a=GammaA([]),
        gamma_s=GammaS(
            GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2])
        ),
        gamma_z=GammaZ(
            Safrole.compute_ring_root(
                [keys.bandersnatch for keys in create_validator_data_from_keys()]
            )
        ),
        offenders=PsiO([]),
    )

    # Create block for first slot of next epoch
    first_slot_in_next_epoch = U32(EPOCH_LENGTH)
    entropy = Bytes[32](bytes([42] * 32))
    new_block = create_block(slot=first_slot_in_next_epoch, tickets=[])

    # Apply the transition
    new_state = Safrole.transition(deepcopy(initial_state), new_block, entropy)

    # Calculate expected new η₀ value
    expected_new_eta0 = Hash.blake2b(bytes(initial_state.eta[0]) + bytes(entropy))

    # Check that entropy was rotated:
    # η'₁ = η₀, η'₂ = η₁, η'₃ = η₂
    assert new_state.eta[1] == initial_state.eta[0], "η₁ should be previous η₀"
    assert new_state.eta[2] == initial_state.eta[1], "η₂ should be previous η₁"
    assert new_state.eta[3] == initial_state.eta[2], "η₃ should be previous η₂"

    # And η₀ should be updated with accumulated entropy
    assert new_state.eta[0] == Bytes[32](
        expected_new_eta0
    ), "η₀ should contain new accumulated entropy"


def test_entropy_used_for_fallback_sealing():
    """Test that entropy is correctly used for fallback sealing"""
    # This test should verify that η₃ is used for fallback sealing
    # Implementation depends on the exact details of how fallback sealing is implemented
    pass
