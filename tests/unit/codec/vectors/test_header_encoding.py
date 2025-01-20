"""Tests for header encoding."""
import json
from pathlib import Path
from jam.types.block import Header

def test_header_0_encoding():
    """Test encoding/decoding of Header against test vector 0."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "header_0.json", "r") as f:
        header_json = json.load(f)
    
    with open(test_dir / "header_0.bin", "rb") as f:
        expected_bytes = f.read()


    header = Header.from_json(header_json)

    # Test encoding
    encoded = header.encode()
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

    header = Header.from_json(header_json)

    # Test encoding
    encoded = header.encode()
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