from inspect import signature

from py_ark_vrf import vrf_output
import pytest
from tsrkit_types.bytes import Bytes

from jam.operations.handlers.conductor import Conductor
from jam.settings import setup_setting
from jam.state.transitions import SafroleError, SafroleErrorCode
from jam.state.transitions import Safrole
from jam.types.state.eta import Eta
from tsrkit_types.integers import U32
from jam.types.state.kappa import Kappa
from jam.types.state.gamma import GammaP, GammaA, GammaS, GammaSFallback, GammaZ
from jam.types.state.psi import PsiO
from jam.types.state.iota import Iota
from jam.types.state.lambda_ import Lambda_
from jam.types.protocol.ticket import TicketBody, TicketId, TicketAttempt
from jam.utils.dummy.utils import create_dummy_bytes
from tests.unit.safrole.data import create_block, create_state, create_validator_data_from_keys
from jam.utils.constants import EPOCH_LENGTH, TICKET_SUBMISSION_END


def test_ticket_accumulation(db_path):
    """Test that Safrole correctly accumulates ticket.py during the submission period"""
    # Create initial state with a ticket already in gamma_a
    initial_state = create_state(
        tau=U32(5),  # Assume this is within ticket submission period
        eta=Eta([Bytes[32](bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_p=GammaP(create_validator_data_from_keys()),
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

    setup_setting(db_path, 1)

    # Create a ticket envelope for a block
    ticket_envelope1 = Conductor.generate_ticket(initial_state, 0)
    ticket_envelope2 = Conductor.generate_ticket(initial_state, 1)
    ticket1 = TicketBody(
        id=TicketId(vrf_output(ticket_envelope1.signature)), attempt=ticket_envelope1.attempt
    )
    ticket2 = TicketBody(
        id=TicketId(vrf_output(ticket_envelope2.signature)), attempt=ticket_envelope2.attempt
    )

    # Calculate slot within submission period
    slot_within_submission = U32(5 - (5 % EPOCH_LENGTH) + TICKET_SUBMISSION_END - 1)

    # Create a block with a ticket during submission period
    new_block = create_block(
        slot=slot_within_submission, tickets=[ticket_envelope2, ticket_envelope1]
    )

    # Apply the transition
    new_state = Safrole.transition(
        initial_state, initial_state, new_block, Bytes[32](create_dummy_bytes(32))
    )

    # Check that the new ticket was accumulated
    assert len(new_state.gamma.a) == 2
    # Get the ticket bodies
    tickets = sorted(new_state.gamma.a, key=lambda t: bytes(t.id))
    assert tickets[1].id == ticket1.id
    assert tickets[0].id == ticket2.id


def test_ticket_submission_outside_period(db_path):
    """Test that Safrole rejects ticket.py outside the submission period"""
    # Create initial state
    initial_state = create_state(
        tau=U32(5),
        eta=Eta([Bytes[32](bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_p=GammaP(create_validator_data_from_keys()),
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
    setup_setting(db_path, 1)

    # Calculate a slot after submission period
    slot_after_submission = U32(5 - (5 % EPOCH_LENGTH) + TICKET_SUBMISSION_END + 1)

    # Create a ticket envelope
    ticket_envelope = Conductor.generate_ticket(initial_state, 0)

    # Create a block with ticket.py after the submission period
    new_block = create_block(slot=slot_after_submission, tickets=[ticket_envelope])

    # Verify that the transition raises the expected error
    with pytest.raises(SafroleError) as excinfo:
        Safrole.transition(
            initial_state, initial_state, new_block, Bytes[32](create_dummy_bytes(32))
        )

    assert excinfo.value.code == SafroleErrorCode.UNEXPECTED_TICKET


def test_ticket_duplicate_rejection(db_path):
    """Test that Safrole correctly rejects duplicate ticket.py"""
    # Create initial state
    initial_state = create_state(
        tau=U32(5),  # Assume this is within ticket submission period
        eta=Eta([Bytes[32](bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_p=GammaP(create_validator_data_from_keys()),
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

    setup_setting(db_path, 1)

    # Create a ticket envelope
    ticket_envelope = Conductor.generate_ticket(initial_state, 0)

    # Calculate slot within submission period
    slot_within_submission = U32(5 - (5 % EPOCH_LENGTH) + TICKET_SUBMISSION_END - 1)

    # Create a block with duplicate ticket.py (same ID)
    duplicate_block = create_block(
        slot=slot_within_submission, tickets=[ticket_envelope, ticket_envelope]  # Same ticket twice
    )

    # Verify that trying to apply duplicate ticket.py raises the expected error
    with pytest.raises(SafroleError) as excinfo:
        Safrole.transition(initial_state, initial_state, duplicate_block, Bytes[32](bytes(32)))

    # Check that the error message indicates duplicate ticket.py not allowed
    assert "Duplicate tickets are not allowed" in str(excinfo.value)


def test_ticket_sorting(db_path):
    """Test that Safrole correctly sorts ticket.py by ID"""
    # Create initial state
    initial_state = create_state(
        tau=U32(5),  # Assume this is within ticket submission period
        eta=Eta([Bytes[32](bytes(32)) for _ in range(4)]),
        lambda_=Lambda_(create_validator_data_from_keys()),
        kappa=Kappa(create_validator_data_from_keys()),
        gamma_p=GammaP(create_validator_data_from_keys()),
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

    settings = setup_setting(db_path, 1)

    # Create multiple ticket envelopes (3 distinct tickets)
    envelopes = [Conductor.generate_ticket(initial_state, i) for i in range(2)]

    settings.clear()

    setup_setting(db_path, 2)
    envelopes.append(Conductor.generate_ticket(initial_state, 0))

    envelopes = sorted(envelopes, key=lambda v: vrf_output(v.signature))

    # Calculate slot within submission period
    slot_within_submission = U32(5 - (5 % EPOCH_LENGTH) + TICKET_SUBMISSION_END - 1)

    # Create IDs that are guaranteed to be different
    ticket_ids = [TicketId(vrf_output(tkt.signature)) for tkt in envelopes]

    # Create a block with the ticket.py
    new_block = create_block(slot=slot_within_submission, tickets=envelopes)

    # Apply the transition
    new_state = Safrole.transition(
        initial_state, initial_state, new_block, Bytes[32](create_dummy_bytes(32))
    )

    # Check that ticket.py were accumulated
    assert len(new_state.gamma.a) == 3

    # Extract the IDs of accumulated ticket.py
    accumulated_ids = [ticket.id for ticket in new_state.gamma.a]

    # Check all our tickets made it into the accumulator
    for ticket_id in ticket_ids:
        assert ticket_id in accumulated_ids, f"Ticket {ticket_id} should be in accumulator"

    # Verify ticket.py are sorted by ID
    expected_order = sorted(ticket_ids)
    assert accumulated_ids == expected_order, "Tickets should be sorted by ID"
