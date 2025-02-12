"""Tests for ticket-related types."""
import json
from pathlib import Path
from jam.types.extrinsics.tickets import TicketsExtrinsic

def test_tickets_extrinsic_encoding():
    """Test encoding/decoding of TicketsExtrinsic against test vectors."""
    # Load test vectors
    test_dir = Path(__file__).parent / "data"
    with open(test_dir / "tickets_extrinsic.json", "r") as f:
        tickets_json = json.load(f)
    
    with open(test_dir / "tickets_extrinsic.bin", "rb") as f:
        expected_bytes = f.read()


    tickets_extrinsic = TicketsExtrinsic.from_json(tickets_json)

    # Test encoding
    encoded = bytearray(tickets_extrinsic.encode_size())
    tickets_extrinsic.encode_into(encoded)

    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = TicketsExtrinsic.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    
    # Verify decoded matches original
    assert len(decoded) == len(tickets_extrinsic)
    for orig, dec in zip(tickets_extrinsic, decoded):
        assert orig.attempt == dec.attempt
        assert orig.signature == dec.signature 