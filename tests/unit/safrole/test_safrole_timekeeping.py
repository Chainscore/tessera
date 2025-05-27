from copy import deepcopy

import pytest
from jam.consensus.safrole.errors import SafroleError, SafroleErrorCode
from jam.consensus.safrole.safrole import Safrole
from jam.types.state.eta import Eta
from jam.types.base.integers.fixed import U32
from jam.types.state.kappa import Kappa
from jam.types.state.gamma import GammaK, GammaA, GammaS, GammaSFallback, GammaZ
from jam.types.state.psi import PsiO
from jam.types.state.iota import Iota
from jam.types.state.lambda_ import Lambda_
from jam.types.protocol.crypto import ByteArray32
from jam.utils.dummy.utils import create_dummy_bytes
from tests.unit.safrole.data import create_block, create_state, create_validator_data_from_keys
from jam.utils.constants import EPOCH_LENGTH


def test_slot_increment():
    """Test that Safrole correctly handles normal slot increments"""
    # Create initial state at slot 5
    initial_state = create_state(
        tau=U32(5),
        eta=Eta([ByteArray32(bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_k=GammaK(create_validator_data_from_keys()),
        iota=Iota(create_validator_data_from_keys()),
        gamma_a=GammaA([]),
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in create_validator_data_from_keys()])),
        offenders=PsiO([])
    )
    
    # Create block with next slot
    new_block = create_block(slot=U32(6), tickets=[])
    
    # Apply transition
    new_state = Safrole.transition(deepcopy(initial_state), new_block, ByteArray32(create_dummy_bytes(32)))
    
    # Verify tau was updated correctly
    assert new_state.tau == U32(6)


def test_slot_jump():
    """Test that Safrole correctly handles slot jumps (multiple slots at once)"""
    # Create initial state at slot 5
    initial_state = create_state(
        tau=U32(5),
        eta=Eta([ByteArray32(bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_k=GammaK(create_validator_data_from_keys()),
        iota=Iota(create_validator_data_from_keys()),
        gamma_a=GammaA([]),
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in create_validator_data_from_keys()])),
        offenders=PsiO([])
    )
    
    # Create block with a slot jump (several slots ahead)
    new_block = create_block(slot=U32(15), tickets=[])
    
    # Apply transition
    new_state = Safrole.transition(deepcopy(initial_state), new_block, ByteArray32(create_dummy_bytes(32)))
    
    # Verify tau was updated correctly
    assert new_state.tau == U32(15)


def test_epoch_boundary_slot():
    """Test that Safrole correctly handles slots at epoch boundaries"""
    # Create initial state at the last slot of an epoch
    last_slot_in_epoch = U32(EPOCH_LENGTH - 1)
    initial_state = create_state(
        tau=last_slot_in_epoch,
        eta=Eta([ByteArray32(bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_k=GammaK(create_validator_data_from_keys()),
        iota=Iota(create_validator_data_from_keys()),
        gamma_a=GammaA([]),
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in create_validator_data_from_keys()])),
        offenders=PsiO([])
    )
    
    # Create block for the first slot of the next epoch
    first_slot_in_next_epoch = U32(EPOCH_LENGTH)
    new_block = create_block(slot=first_slot_in_next_epoch, tickets=[])
    
    # Apply transition
    new_state = Safrole.transition(deepcopy(initial_state), new_block, ByteArray32(create_dummy_bytes(32)))
    
    # Verify tau was updated correctly
    assert new_state.tau == first_slot_in_next_epoch
    
    # Also verify epoch change is detected correctly
    assert int(initial_state.tau) // EPOCH_LENGTH != int(new_state.tau) // EPOCH_LENGTH 