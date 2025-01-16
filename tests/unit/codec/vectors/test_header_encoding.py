"""Tests for header encoding."""
import json
from pathlib import Path

from jam.types.block import Header
from jam.types.extrinsics.tickets import TicketAttempt, TicketBody, TicketId
from jam.types.header import OffendersMark, TicketsMark
from jam.types.protocol.core import TimeSlot, ValidatorIndex
from jam.types.protocol.crypto import (
    Ed25519Public, Entropy, HeaderHash, StateRoot, OpaqueHash,
    BandersnatchPublic, BandersnatchVrfSignature
)
from jam.types.protocol.epoch import EpochMark
from jam.types.protocol.validators import ValidatorArray

def test_header_0_encoding():
    """Test encoding/decoding of Header against test vector 0."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "header_0.json", "r") as f:
        header_json = json.load(f)
    
    with open(test_dir / "header_0.bin", "rb") as f:
        expected_bytes = f.read()

    # Create Header from JSON
    epoch_mark = None
    tickets_mark = None
    if header_json["epoch_mark"] is not None:
        epoch_mark = EpochMark(
            entropy=Entropy(bytes.fromhex(header_json["epoch_mark"]["entropy"][2:])),
            tickets_entropy=Entropy(bytes.fromhex(header_json["epoch_mark"]["tickets_entropy"][2:])),
            validators=ValidatorArray(
                [BandersnatchPublic(bytes.fromhex(validator[2:])) for validator in header_json["epoch_mark"]["validators"]]
            )
        )
    if header_json["tickets_mark"] is not None:
        tickets_mark = TicketsMark(
            [TicketBody(TicketId(bytes.fromhex(ticket.id)), TicketAttempt(int(ticket.attempt))) for ticket in header_json["tickets_mark"]]
        )
    header = Header(
        parent=HeaderHash(bytes.fromhex(header_json["parent"][2:])),
        parent_state_root=StateRoot(bytes.fromhex(header_json["parent_state_root"][2:])),
        extrinsic_hash=OpaqueHash(bytes.fromhex(header_json["extrinsic_hash"][2:])),
        slot=TimeSlot(header_json["slot"]),
        epoch_mark=epoch_mark,
        tickets_mark=tickets_mark,
        offenders_mark=OffendersMark(
            [Ed25519Public(bytes.fromhex(offender[2:])) for offender in header_json["offenders_mark"]]
        ),
        author_index=ValidatorIndex(header_json["author_index"]),
        entropy_source=BandersnatchVrfSignature(bytes.fromhex(header_json["entropy_source"][2:])),
        seal=BandersnatchVrfSignature(bytes.fromhex(header_json["seal"][2:]))
    )

    # Test encoding
    encoded = bytearray(header.encode_size())
    header.encode_into(encoded)
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = Header.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    # Verify decoded matches original
    assert decoded.parent == header.parent
    assert decoded.slot == header.slot
    assert decoded.epoch_mark == header.epoch_mark
    assert decoded.tickets_mark == header.tickets_mark
    assert decoded.offenders_mark == header.offenders_mark
    assert decoded.author_index == header.author_index
    assert decoded.entropy_source == header.entropy_source
    assert decoded.seal == header.seal

def test_header_1_encoding():
    """Test encoding/decoding of Header against test vector 1."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "header_1.json", "r") as f:
        header_json = json.load(f)
    
    with open(test_dir / "header_1.bin", "rb") as f:
        expected_bytes = f.read()

    # Create Header from JSON
    epoch_mark = None
    tickets_mark = None
    if header_json["epoch_mark"] is not None:
        epoch_mark = EpochMark(
            entropy=Entropy(bytes.fromhex(header_json["epoch_mark"]["entropy"][2:])),
            tickets_entropy=Entropy(bytes.fromhex(header_json["epoch_mark"]["tickets_entropy"][2:])),
            validators=ValidatorArray(
                [BandersnatchPublic(bytes.fromhex(validator[2:])) for validator in header_json["epoch_mark"]["validators"]]
            )
        )
    if header_json["tickets_mark"] is not None:
        tickets_mark = TicketsMark(
            [TicketBody(TicketId(bytes.fromhex(ticket['id'][2:])), TicketAttempt(int(ticket['attempt']))) for ticket in header_json["tickets_mark"]]
        )
    header = Header(
        parent=HeaderHash(bytes.fromhex(header_json["parent"][2:])),
        parent_state_root=StateRoot(bytes.fromhex(header_json["parent_state_root"][2:])),
        extrinsic_hash=OpaqueHash(bytes.fromhex(header_json["extrinsic_hash"][2:])),
        slot=TimeSlot(header_json["slot"]),
        epoch_mark=epoch_mark,
        tickets_mark=tickets_mark,
        offenders_mark=OffendersMark(
            [Ed25519Public(bytes.fromhex(offender[2:])) for offender in header_json["offenders_mark"]]
        ),
        author_index=ValidatorIndex(header_json["author_index"]),
        entropy_source=BandersnatchVrfSignature(bytes.fromhex(header_json["entropy_source"][2:])),
        seal=BandersnatchVrfSignature(bytes.fromhex(header_json["seal"][2:]))
    )

    # Test encoding
    encoded = bytearray(header.encode_size())
    header.encode_into(encoded)
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = Header.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    # Verify decoded matches original
    assert decoded.parent == header.parent
    assert decoded.slot == header.slot
    assert decoded.epoch_mark == header.epoch_mark
    assert decoded.tickets_mark == header.tickets_mark
    assert decoded.offenders_mark == header.offenders_mark
    assert decoded.author_index == header.author_index
    assert decoded.entropy_source == header.entropy_source
    assert decoded.seal == header.seal