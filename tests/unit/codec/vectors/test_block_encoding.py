"""Tests for block encoding."""
import json
from pathlib import Path
from jam.types.block import Block


def test_block_encoding():
    """Test encoding/decoding of Block against test vectors."""
    test_dir = Path(__file__).parent / "data"

    # Load test vectors
    with open(test_dir / "block.json", "r") as f:
        block_json = json.load(f)

    with open(test_dir / "block.bin", "rb") as f:
        expected_bytes = f.read()

    block = Block.from_json(block_json)

    # Test encoding
    encoded = bytearray(block.encode_size())
    block.encode_into(encoded)
    assert bytes(encoded) == expected_bytes
    assert block.encode_size() == len(expected_bytes)

    # Test decoding
    decoded, size = Block.decode_from(expected_bytes)
    # assert size == len(expected_bytes)

    # Verify decoded matches original
    assert decoded.header == block.header
    assert decoded.extrinsic == block.extrinsic
    # assert decoded == block
