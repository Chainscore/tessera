"""Tests for refine context encoding."""
import json
from pathlib import Path

from jam.types.base.vector import Vector
from jam.types.work import RefineContext
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import HeaderHash, StateRoot, BeefyRoot, OpaqueHash

def test_refine_context_encoding():
    """Test encoding/decoding of RefineContext against test vectors."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "refine_context.json", "r") as f:
        context_json = json.load(f)
    
    with open(test_dir / "refine_context.bin", "rb") as f:
        expected_bytes = f.read()

    # Create RefineContext from JSON
    context = RefineContext(
        anchor=HeaderHash(bytes.fromhex(context_json["anchor"][2:])),
        state_root=StateRoot(bytes.fromhex(context_json["state_root"][2:])),
        beefy_root=BeefyRoot(bytes.fromhex(context_json["beefy_root"][2:])),
        lookup_anchor=HeaderHash(bytes.fromhex(context_json["lookup_anchor"][2:])),
        lookup_anchor_slot=TimeSlot(context_json["lookup_anchor_slot"]),
        prerequisites=Vector(
            [OpaqueHash(bytes.fromhex(hash_hex[2:])) for hash_hex in context_json["prerequisites"]]
        )
    )

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