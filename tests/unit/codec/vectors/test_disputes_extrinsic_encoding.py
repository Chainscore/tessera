"""Tests for disputes extrinsic encoding."""
import json
from pathlib import Path
from jam.types.extrinsics.disputes import DisputesExtrinsic


def test_disputes_extrinsic_encoding():
    """Test encoding/decoding of DisputesExtrinsic against test vectors."""
    test_dir = Path(__file__).parent / "data"

    # Load test vectors
    with open(test_dir / "disputes_extrinsic.json", "r") as f:
        disputes_json = json.load(f)

    with open(test_dir / "disputes_extrinsic.bin", "rb") as f:
        expected_bytes = f.read()

    # Create DisputesExtrinsic from JSON
    disputes = DisputesExtrinsic.from_json(disputes_json)

    # Test encoding
    encoded = bytearray(disputes.encode_size())
    disputes.encode_into(encoded)
    assert disputes.encode_size() == len(expected_bytes)
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = DisputesExtrinsic.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    assert decoded == disputes
