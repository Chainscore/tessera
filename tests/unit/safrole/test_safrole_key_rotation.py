from copy import deepcopy

import pytest

from jam.state.transitions import Safrole
from tsrkit_types.bytes import Bytes
from jam.types.state.eta import Eta
from tsrkit_types.integers import U32
from jam.types.state.kappa import Kappa
from jam.types.state.gamma import GammaK, GammaA, GammaS, GammaSFallback, GammaZ
from jam.types.state.psi import PsiO
from jam.types.state.iota import Iota
from jam.types.state.lambda_ import Lambda_
from jam.utils.dummy.utils import create_dummy_bytes
from tests.unit.safrole.data import create_block, create_state, create_validator_data_from_keys
from jam.utils.constants import EPOCH_LENGTH


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_key_rotation_at_epoch_boundary():
    """Test that Safrole correctly rotates validator keys at epoch boundaries"""
    # Create validator data
    validators = create_validator_data_from_keys()

    # Create initial state at the last slot of an epoch
    last_slot_in_epoch = U32(EPOCH_LENGTH - 1)
    initial_state = create_state(
        tau=last_slot_in_epoch,
        eta=Eta([Bytes[32](bytes([i + 1] * 32)) for i in range(4)]),
        lambda_=Lambda_(validators),
        kappa=Kappa(validators),
        gamma_k=GammaK(validators),
        iota=Iota(validators),
        gamma_a=GammaA([]),
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in validators * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in validators])),
        offenders=PsiO([]),
    )

    # Create a block for the first slot of the next epoch
    first_slot_in_next_epoch = U32(EPOCH_LENGTH)
    new_block = create_block(slot=first_slot_in_next_epoch, tickets=[])

    # Apply the transition
    new_state = Safrole.transition(
        deepcopy(initial_state), new_block, Bytes[32](create_dummy_bytes(32))
    )

    # Verify key rotation
    # λ' = κ (lambda becomes previous kappa)
    assert new_state.lambda_ == initial_state.kappa

    # κ' = γ_k (kappa becomes previous gamma_k)
    assert new_state.kappa == initial_state.gamma.k

    # γ'_k = ι (gamma_k becomes previous iota with offenders filtered)
    assert len(new_state.gamma.k) == len(initial_state.iota)
    for i in range(len(new_state.gamma.k)):
        assert new_state.gamma.k[i] == initial_state.iota[i]

    # Verify that the ring root is updated
    new_ring_root = Bytes[144](
        Safrole.compute_ring_root([keys.bandersnatch for keys in new_state.gamma.k])
    )
    assert new_state.gamma.z == new_ring_root


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_offender_filtering():
    """Test that Safrole correctly filters out offenders during epoch transitions"""
    # Create validator data
    validators = create_validator_data_from_keys()

    # Mark one validator as an offender
    offender_ed25519 = validators[0].ed25519

    # Create an initial state in the last slot of an epoch with offenders
    last_slot_in_epoch = U32(EPOCH_LENGTH - 1)
    initial_state = create_state(
        tau=last_slot_in_epoch,
        eta=Eta([Bytes[32](bytes([i + 1] * 32)) for i in range(4)]),
        lambda_=Lambda_(validators),
        kappa=Kappa(validators),
        gamma_k=GammaK(validators),
        iota=Iota(validators),
        gamma_a=GammaA([]),
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in validators * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in validators])),
        offenders=PsiO([offender_ed25519]),
    )

    # Create a block for the first slot of the next epoch
    first_slot_in_next_epoch = U32(EPOCH_LENGTH)
    new_block = create_block(slot=first_slot_in_next_epoch, tickets=[])

    # Apply the transition
    new_state = Safrole.transition(
        deepcopy(initial_state), new_block, Bytes[32](create_dummy_bytes(32))
    )

    # Check that the offender was replaced with a null key in gamma_k
    filtered_validators = new_state.gamma.k
    for i, validator in enumerate(filtered_validators):
        if i == 0:  # The first validator was the offender
            assert validator.bandersnatch == Bytes[32](
                bytes(32)
            ), "Offender should be replaced with null key"
            assert validator.ed25519 == Bytes[32](
                bytes(32)
            ), "Offender should be replaced with null key"
        else:
            assert (
                validator.bandersnatch == validators[i].bandersnatch
            ), "Non-offenders should remain unchanged"


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_all_validators_are_offenders():
    """Test behavior when all validators are marked as offenders"""
    # Create validator data
    validators = create_validator_data_from_keys()

    # Mark all validators as offenders
    offenders = PsiO([validator.ed25519 for validator in validators])

    # Create an initial state in the last slot of an epoch with all offenders
    last_slot_in_epoch = U32(EPOCH_LENGTH - 1)
    initial_state = create_state(
        tau=last_slot_in_epoch,
        eta=Eta([Bytes[32](bytes([i + 1] * 32)) for i in range(4)]),
        lambda_=Lambda_(validators),
        kappa=Kappa(validators),
        gamma_k=GammaK(validators),
        iota=Iota(validators),
        gamma_a=GammaA([]),
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in validators * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in validators])),
        offenders=offenders,
    )

    # Create a block for the first slot of the next epoch
    first_slot_in_next_epoch = U32(EPOCH_LENGTH)
    new_block = create_block(slot=first_slot_in_next_epoch, tickets=[])

    # Apply the transition
    new_state = Safrole.transition(
        deepcopy(initial_state), new_block, Bytes[32](create_dummy_bytes(32))
    )

    # Verify all validators in gamma_k are replaced with null keys
    for validator in new_state.gamma.k:
        assert validator.bandersnatch == Bytes[32](bytes(32)), "All validators should be null keys"
        assert validator.ed25519 == Bytes[32](bytes(32)), "All validators should be null keys"
