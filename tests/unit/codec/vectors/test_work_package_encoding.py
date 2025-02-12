"""Tests for work package encoding."""
import json
from pathlib import Path
from jam.types.work.package import WorkPackage


def test_work_package_encoding():
    """Test encoding/decoding of WorkPackage against test vectors."""
    test_dir = Path(__file__).parent / "data"

    # Load test vectors
    with open(test_dir / "work_package.json", "r") as f:
        package_json = json.load(f)

    with open(test_dir / "work_package.bin", "rb") as f:
        expected_bytes = f.read()

    # Create WorkPackage from JSON
    package = WorkPackage.from_json(package_json)

    # Test encoding
    encoded = bytearray(package.encode_size())
    package.encode_into(encoded)
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = WorkPackage.decode_from(expected_bytes)
    assert size == len(expected_bytes)

    # Verify decoded matches original
    assert decoded.authorization == package.authorization
    assert decoded.auth_code_host == package.auth_code_host
    assert decoded.authorizer == package.authorizer
    assert decoded.context == package.context
    assert len(decoded.items) == len(package.items)
    for dec_item, orig_item in zip(decoded.items, package.items):
        assert dec_item == orig_item
