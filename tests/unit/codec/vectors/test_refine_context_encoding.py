"""Tests for refine context encoding."""
import json
from pathlib import Path
from jam.types.work import RefineContext


def test_refine_context_encoding():
    """Test encoding/decoding of RefineContext against test vectors."""
    test_dir = Path(__file__).parent / "data"

    # Load test vectors
    with open(test_dir / "refine_context.json", "r") as f:
        context_json = json.load(f)

    with open(test_dir / "refine_context.bin", "rb") as f:
        expected_bytes = f.read()

    # Create RefineContext from JSON
    context = RefineContext.from_json(context_json)

    # Test encoding
    encoded = bytearray(context.encode_size())
    context.encode_into(encoded)
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = RefineContext.decode_from(expected_bytes)
    assert size == len(expected_bytes)

    # Verify decoded matches original
    assert decoded.anchor == context.anchor
    assert decoded.state_root == context.state_root
    assert decoded.beefy_root == context.beefy_root
    assert decoded.lookup_anchor == context.lookup_anchor
    assert decoded.lookup_anchor_slot == context.lookup_anchor_slot
    assert len(decoded.prerequisites) == len(context.prerequisites)
    for dec_hash, orig_hash in zip(decoded.prerequisites, context.prerequisites):
        assert dec_hash == orig_hash
