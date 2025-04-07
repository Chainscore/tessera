import pytest
from jam.consensus.safrole.errors import SafroleError, SafroleErrorCode
from jam.consensus.safrole.safrole import Safrole
from jam.state.components.eta import Eta
from jam.types.base.integers.fixed import U32
from jam.state.components.kappa import Kappa
from jam.consensus.safrole.gamma import GammaK, GammaA, GammaS, GammaSFallback, GammaZ
from jam.state.components.psi import PsiO
from jam.state.components.iota import Iota
from jam.state.components.lambda_ import Lambda_
from jam.types.protocol.crypto import ByteArray32
from jam.types.extrinsics.tickets import TicketBody, TicketId, TicketAttempt, TicketEnvelope
from tests.unit.safrole.data import create_block, create_state, create_validator_data_from_keys, generate_ticket
from jam.utils.constants import EPOCH_LENGTH, TICKET_SUBMISSION_END, MAX_TICKETS_PER_EXTRINSIC


def test_ticket_accumulation():
    """Test that Safrole correctly accumulates tickets during the submission period"""
    # Create tickets
    ticket1 = TicketBody(id=TicketId(bytes([1] * 32)), attempt=TicketAttempt(0))
    
    # Create initial state with a ticket already in gamma_a
    initial_state = create_state(
        tau=U32(5),  # Assume this is within ticket submission period
        eta=Eta([ByteArray32(bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_k=GammaK(create_validator_data_from_keys()),
        iota=Iota(create_validator_data_from_keys()),
        gamma_a=GammaA([ticket1]),
        gamma_s=GammaS(GammaSFallback([keys.bandersnatch for keys in create_validator_data_from_keys() * 2])),
        gamma_z=GammaZ(Safrole.compute_ring_root([keys.bandersnatch for keys in create_validator_data_from_keys()])),
        offenders=PsiO([])
    )
    
    # Create a ticket envelope for a block
    ticket_envelope = generate_ticket()
    
    # Calculate slot within submission period
    slot_within_submission = U32(5 - (5 % EPOCH_LENGTH) + TICKET_SUBMISSION_END - 1)
    
    # Mock the vrf_output function to return a predictable value
    original_vrf_output = Safrole.vrf_output
    ticket2_id = TicketId(bytes([2] * 32))
    Safrole.vrf_output = lambda _: ticket2_id
    
    try:
        # Create a block with a ticket during submission period
        new_block = create_block(
            slot=slot_within_submission, 
            tickets=[ticket_envelope]
        )
        
        # Apply the transition
        new_state = Safrole.transition(initial_state, new_block, ByteArray32(bytes(32)))
        
        # Check that the new ticket was accumulated
        assert len(new_state.gamma.a) == 2
        # Get the ticket bodies
        tickets = sorted(new_state.gamma.a, key=lambda t: bytes(t.id))
        assert tickets[0].id == ticket1.id
        assert tickets[1].id == ticket2_id
    finally:
        # Restore the original function
        Safrole.vrf_output = original_vrf_output


def test_ticket_submission_outside_period():
    """Test that Safrole rejects tickets outside the submission period"""
    # Create initial state
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
    
    # Calculate a slot after submission period
    slot_after_submission = U32(5 - (5 % EPOCH_LENGTH) + TICKET_SUBMISSION_END + 1)
    
    # Create a ticket envelope
    ticket_envelope = generate_ticket()
    
    # Create a block with tickets after the submission period
    new_block = create_block(
        slot=slot_after_submission, 
        tickets=[ticket_envelope]
    )
    
    # Verify that the transition raises the expected error
    with pytest.raises(SafroleError) as excinfo:
        Safrole.transition(initial_state, new_block, ByteArray32(bytes(32)))
    
    assert excinfo.value.code == SafroleErrorCode.UNEXPECTED_TICKET


def test_ticket_duplicate_rejection():
    """Test that Safrole correctly rejects duplicate tickets"""
    # Create initial state
    initial_state = create_state(
        tau=U32(5),  # Assume this is within ticket submission period
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
    
    # Create a ticket envelope
    ticket_envelope = generate_ticket()
    
    # Calculate slot within submission period
    slot_within_submission = U32(5 - (5 % EPOCH_LENGTH) + TICKET_SUBMISSION_END - 1)
    
    # Mock the vrf_output function to return the same ID for all tickets
    original_vrf_output = Safrole.vrf_output
    duplicate_id = TicketId(bytes([1] * 32))
    Safrole.vrf_output = lambda _: duplicate_id
    
    try:
        # Create a block with duplicate tickets (same ID)
        duplicate_block = create_block(
            slot=slot_within_submission, 
            tickets=[ticket_envelope, ticket_envelope]  # Same ticket twice
        )
        
        # Verify that trying to apply duplicate tickets raises the expected error
        with pytest.raises(SafroleError) as excinfo:
            Safrole.transition(initial_state, duplicate_block, ByteArray32(bytes(32)))
        
        # Check that the error message indicates duplicate tickets not allowed
        assert "Duplicate tickets are not allowed" in str(excinfo.value)
    finally:
        # Restore the original function
        Safrole.vrf_output = original_vrf_output

def test_ticket_sorting():
    """Test that Safrole correctly sorts tickets by ID"""
    # Create initial state
    initial_state = create_state(
        tau=U32(5),  # Assume this is within ticket submission period
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
    
    # Create multiple ticket envelopes (3 distinct tickets)
    envelopes = [generate_ticket() for _ in range(3)]
    
    # Calculate slot within submission period
    slot_within_submission = U32(5 - (5 % EPOCH_LENGTH) + TICKET_SUBMISSION_END - 1)
    
    # Mock the vrf_output function to return ticket IDs that are guaranteed to be distinct
    original_vrf_output = Safrole.vrf_output
    
    # Create IDs that are guaranteed to be different
    ticket_ids = [
        TicketId(bytes([100] * 32)),  # Using values well separated to ensure uniqueness
        TicketId(bytes([200] * 32)),
        TicketId(bytes([202] * 32)),
    ]
    
    # Map each ticket envelope to a specific ID to avoid any duplicate IDs
    ticket_map = {id(envelope): ticket_ids[i] for i, envelope in enumerate(envelopes)}
    
    def mock_vrf_output(signature):
        # If the signature belongs to one of our test envelopes, return the mapped ID
        for envelope in envelopes:
            if signature is envelope.signature:  # Using identity comparison
                return ticket_map[id(envelope)]
        # Otherwise return a default ID
        return TicketId(bytes([50] * 32))
    
    Safrole.vrf_output = mock_vrf_output
    
    try:
        # Create a block with the tickets
        new_block = create_block(
            slot=slot_within_submission, 
            tickets=envelopes
        )
        
        # Apply the transition
        new_state = Safrole.transition(initial_state, new_block, ByteArray32(bytes(32)))
        
        # Check that tickets were accumulated
        assert len(new_state.gamma.a) == 3
        
        # Extract the IDs of accumulated tickets
        accumulated_ids = [ticket.id for ticket in new_state.gamma.a]
        
        # Check all our tickets made it into the accumulator
        for ticket_id in ticket_ids:
            assert ticket_id in accumulated_ids, f"Ticket {ticket_id} should be in accumulator"
        
        # Verify tickets are sorted by ID
        expected_order = sorted(ticket_ids)
        assert accumulated_ids == expected_order, "Tickets should be sorted by ID"
    finally:
        # Restore the original function
        Safrole.vrf_output = original_vrf_output