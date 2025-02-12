"""Tests for assurances extrinsic encoding."""
import json
from pathlib import Path

from jam.types.extrinsics.assurances import AssurancesExtrinsic


def test_assurances_extrinsic_encoding():
    """Test encoding/decoding of AssurancesExtrinsic against test vectors."""
    test_dir = Path(__file__).parent / "data"

    # Load test vectors
    with open(test_dir / "assurances_extrinsic.json", "r") as f:
        assurances_json = json.loads(f.read())

    with open(test_dir / "assurances_extrinsic.bin", "rb") as f:
        expected_bytes = f.read()

    # Create AssurancesExtrinsic from JSON
    assurances = AssurancesExtrinsic.from_json(assurances_json)

    # Test encoding
    encoded = assurances.encode()
    assert encoded == expected_bytes

    # # Test decoding
    decoded, size = AssurancesExtrinsic.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    assert decoded == assurances
