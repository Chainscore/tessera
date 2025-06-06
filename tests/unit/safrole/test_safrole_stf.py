from copy import deepcopy

import pytest
from tsrkit_types.bytes import Bytes

from jam.consensus.safrole.errors import SafroleError, SafroleErrorCode
from jam.consensus.safrole.safrole import Safrole
from jam.types.state.eta import Eta
from tsrkit_types.integers import U32
from jam.types.state.kappa import Kappa
from jam.types.state.gamma import GammaK, GammaA, GammaS, GammaSFallback, GammaZ
from jam.types.state.psi import PsiO
from jam.types.state.iota import Iota
from jam.types.state.lambda_ import Lambda_
from jam.types.extrinsics.tickets import TicketBody, TicketId, TicketAttempt
from jam.utils.dummy.utils import create_dummy_bytes
from tests.unit.safrole.data import create_block, create_state, create_validator_data_from_keys
from jam.utils.constants import EPOCH_LENGTH, TICKET_SUBMISSION_END


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_safrole_timekeeping():
    """Test that Safrole correctly updates the timeslot (tau)"""
    # Create initial state
    eta = Eta([Bytes[32](bytes(32)) for _ in range(4)])
    lambda_ = Lambda_(create_validator_data_from_keys())
    kappa = Kappa(create_validator_data_from_keys())
    gamma_k = GammaK(create_validator_data_from_keys())
    gamma_a = GammaA([])
    gamma_s = GammaS(GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2]))
    gamma_z = GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in create_validator_data_from_keys()]))
    iota = Iota(create_validator_data_from_keys())
    offenders = PsiO([])
    initial_state = create_state(
        tau=U32(5),
        eta=eta,
        lambda_=lambda_,
        kappa=kappa,
        gamma_k=gamma_k,
        iota=iota,
        gamma_a=gamma_a,
        gamma_s=gamma_s,
        gamma_z=gamma_z,
        offenders=offenders
    )
    
    # Create a block with a higher slot
    new_block = create_block(slot=U32(6), tickets=[])
    
    # Apply the transition
    new_state = Safrole.transition(deepcopy(initial_state), new_block, Bytes[32](create_dummy_bytes(32)))
    
    # Check that the timeslot was updated
    assert new_state.tau == U32(6)


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_safrole_entropy_accumulation():
    """Test that Safrole correctly accumulates entropy"""
    # Create initial state with known entropy values
    test_entropy = [Bytes[32](bytes([i+1] * 32)) for i in range(4)]
    eta = Eta(test_entropy)
    initial_state = create_state(
        tau=U32(5),
        eta=eta,
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_k=GammaK(create_validator_data_from_keys()),
        iota=Iota(create_validator_data_from_keys()),
        gamma_a=GammaA([]),
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in create_validator_data_from_keys()])),
        offenders=PsiO([])
    )
    
    # Create a block with epoch mark to trigger entropy accumulation
    new_block = create_block(slot=U32(6), tickets=[])
    
    # Apply the transition
    new_state = Safrole.transition(deepcopy(initial_state), new_block, Bytes[32](create_dummy_bytes(32)))
    # Check that the entropy was accumulated (η'₀ = H(η₀ || VRF_output(H_v)))
    assert new_state.eta[0] != initial_state.eta[0], "Entropy should be updated"
    # Other entropy slots should remain unchanged
    assert new_state.eta[1] == initial_state.eta[1]
    assert new_state.eta[2] == initial_state.eta[2]
    assert new_state.eta[3] == initial_state.eta[3]


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_safrole_ticket_accumulation():
    """Test that Safrole correctly accumulates tickets during the submission period"""
    # Create tickets
    ticket1 = TicketBody(id=TicketId(bytes([1] * 32)), attempt=TicketAttempt(0))
    ticket2 = TicketBody(id=TicketId(bytes([2] * 32)), attempt=TicketAttempt(0))
    
    # Create initial state with some tickets already in gamma_a
    initial_state = create_state(
        tau=U32(5),  # Assume this is within ticket submission period
        eta=Eta([Bytes[32](bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_k=GammaK(create_validator_data_from_keys()),
        iota=Iota(create_validator_data_from_keys()),
        gamma_a=GammaA([ticket1]),
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in create_validator_data_from_keys()])),
        offenders=PsiO([])
    )
    
    # Create ticket extrinsics for a block
    ticket_envelope = Safrole.generate_ticket()  # This will create a ticket with default values
    
    # Create a block with ticket during submission period
    # Assume slot 6 is within ticket submission period (less than TICKET_SUBMISSION_END)
    slot_within_submission = U32(5 - (5 % EPOCH_LENGTH) + TICKET_SUBMISSION_END - 1)
    new_block = create_block(slot=slot_within_submission, tickets=[ticket_envelope])
    
    # Mock the vrf_output function to return ticket2's id
    original_vrf_output = Safrole.vrf_output
    Safrole.vrf_output = lambda _: ticket2.id
    
    try:
        # Apply the transition
        new_state = Safrole.transition(deepcopy(initial_state), new_block, Bytes[32](create_dummy_bytes(32)))
        
        # Check that the new ticket was accumulated
        assert len(new_state.gamma.a) == 2
        assert ticket1 in new_state.gamma.a
        assert ticket2 in new_state.gamma.a
    finally:
        # Restore the original function
        Safrole.vrf_output = original_vrf_output


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_safrole_ticket_submission_outside_period():
    """Test that Safrole rejects tickets outside the submission period"""
    # Create initial state
    initial_state = create_state(
        tau=U32(5),
        eta=Eta([Bytes[32](bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_k=GammaK(create_validator_data_from_keys()),
        iota=Iota(create_validator_data_from_keys()),
        gamma_a=GammaA([]),
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in create_validator_data_from_keys()])),
        offenders=PsiO([])
    )
    
    # Create a block with tickets after the submission period
    # Calculate a slot that is after TICKET_SUBMISSION_END
    slot_after_submission = U32(5 - (5 % EPOCH_LENGTH) + TICKET_SUBMISSION_END + 1)
    ticket_envelope = Safrole.generate_ticket()
    new_block = create_block(slot=slot_after_submission, tickets=[ticket_envelope])
    
    # Verify that the transition raises the expected error
    with pytest.raises(SafroleError) as excinfo:
        Safrole.transition(deepcopy(initial_state), new_block, Bytes[32](create_dummy_bytes(32)))
    
    assert excinfo.value.code == SafroleErrorCode.UNEXPECTED_TICKET


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_safrole_epoch_transition():
    """Test that Safrole correctly handles epoch transitions"""
    # Create validator data
    validators = create_validator_data_from_keys()
    
    # Create an initial state in the last slot of an epoch
    last_slot_in_epoch = U32(EPOCH_LENGTH - 1)
    initial_state = create_state(
        tau=last_slot_in_epoch,
        eta=Eta([Bytes[32](bytes([i+1] * 32)) for i in range(4)]),
        lambda_=Lambda_(validators),
        kappa=Kappa(validators),
        gamma_k=GammaK(validators),
        iota=Iota(validators),
        gamma_a=GammaA([]), 
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in validators * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in validators])),
        offenders=PsiO([])
    )
    
    # Create a block for the first slot of the next epoch
    first_slot_in_next_epoch = U32(EPOCH_LENGTH)
    new_block = create_block(slot=first_slot_in_next_epoch, tickets=[])
    
    # Apply the transition
    new_state = Safrole.transition(deepcopy(initial_state), new_block, Bytes[32](create_dummy_bytes(32)))
    
    # Verify epoch transition effects
    
    # 1. Check key rotation (γ'ᵏ = Φ(ιota), κ' = γᵏ, λ' = κ)
    assert new_state.gamma.k == initial_state.iota
    assert new_state.kappa == initial_state.gamma.k
    assert new_state.lambda_ == initial_state.kappa
    
    # 2. Check entropy rotation (η'₁ = η₀, η'₂ = η₁, η'₃ = η₂)
    assert new_state.eta[1] == initial_state.eta[0]
    assert new_state.eta[2] == initial_state.eta[1]
    assert new_state.eta[3] == initial_state.eta[2]
    
    # 3. Check ticket accumulator reset
    assert len(new_state.gamma.a) == 0
    
    # 4. Ring root should be not be updated since the validator set is same
    # TODO - write a test with chanegd val set
    assert new_state.gamma.z == initial_state.gamma.z


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_safrole_fallback_mode():
    """Test that Safrole correctly uses fallback seal keys when not enough tickets"""
    # Create validator data
    validators = create_validator_data_from_keys()
    
    # Create an initial state in the last slot of an epoch, but with insufficient tickets
    last_slot_in_epoch = U32(EPOCH_LENGTH - 1)
    initial_state = create_state(
        tau=last_slot_in_epoch,
        eta=Eta([Bytes[32](bytes([i+1] * 32)) for i in range(4)]),
        lambda_=Lambda_(validators),
        kappa=Kappa(validators),
        gamma_k=GammaK(validators),
        iota=Iota(validators),
        gamma_a=GammaA([]),  # Empty ticket accumulator (insufficient tickets)
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in validators * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in validators])),
        offenders=PsiO([])
    )
    
    # Create a block for the first slot of the next epoch
    first_slot_in_next_epoch = U32(EPOCH_LENGTH)
    new_block = create_block(slot=first_slot_in_next_epoch, tickets=[])
    
    # Apply the transition
    new_state = Safrole.transition(deepcopy(initial_state), new_block, Bytes[32](create_dummy_bytes(32)))
    
    # Check that we're using fallback seal keys (GammaSFallback)
    assert isinstance(new_state.gamma.s.unwrap(), GammaSFallback)
    
    # Verify slot keys are determined using F(η'₂, κ')
    # The exact values would depend on implementation details of arrange_fallback


@pytest.mark.skipif(True, reason="Ring commitment takes too long")
def test_safrole_offender_filtering():
    """Test that Safrole correctly filters out offenders during epoch transitions"""
    # Create validator data
    validators = create_validator_data_from_keys()
    
    # Mark one validator as an offender
    offender_ed25519 = validators[0].ed25519
    
    # Create an initial state in the last slot of an epoch with offenders
    last_slot_in_epoch = U32(EPOCH_LENGTH - 1)
    initial_state = create_state(
        tau=last_slot_in_epoch,
        eta=Eta([Bytes[32](bytes([i+1] * 32)) for i in range(4)]),
        lambda_=Lambda_(validators),
        kappa=Kappa(validators),
        gamma_k=GammaK(validators),
        iota=Iota(validators),
        gamma_a=GammaA([]),
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in validators * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in validators])),
        offenders=PsiO([offender_ed25519])
    )
    
    # Create a block for the first slot of the next epoch
    first_slot_in_next_epoch = U32(EPOCH_LENGTH)
    new_block = create_block(slot=first_slot_in_next_epoch, tickets=[])
    
    # Apply the transition
    new_state = Safrole.transition(deepcopy(initial_state), new_block, Bytes[32](create_dummy_bytes(32)))
    
    # Check that the offender was replaced with a null key in gamma_k
    filtered_validators = new_state.gamma.k
    for i, validator in enumerate(filtered_validators):
        if i == 0:  # The first validator was the offender
            assert validator.bandersnatch == Bytes[32](bytes(32)), "Offender should be replaced with null key"
            assert validator.ed25519 == Bytes[32](bytes(32)), "Offender should be replaced with null key"
        else:
            assert validator.bandersnatch == validators[i].bandersnatch, "Non-offenders should remain unchanged"