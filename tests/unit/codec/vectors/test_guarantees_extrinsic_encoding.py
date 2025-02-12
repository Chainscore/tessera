"""Tests for guarantees extrinsic encoding."""
import json
from pathlib import Path
from jam.types.extrinsics.guarantees import GuaranteesExtrinsic


def test_guarantees_extrinsic_encoding():
    """Test encoding/decoding of GuaranteesExtrinsic against test vectors."""
    test_dir = Path(__file__).parent / "data"

    # Load test vectors
    with open(test_dir / "guarantees_extrinsic.json", "r") as f:
        guarantees_json = json.load(f)

    with open(test_dir / "guarantees_extrinsic.bin", "rb") as f:
        expected_bytes = f.read()

    # Create GuaranteesExtrinsic from JSON
    guarantees = GuaranteesExtrinsic.from_json(guarantees_json)

    # Test encoding
    encoded = bytearray(guarantees.encode_size())
    guarantees.encode_into(encoded)
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = GuaranteesExtrinsic.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    assert decoded == guarantees
