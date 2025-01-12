"""Tests for preimages extrinsic encoding."""
import json
from pathlib import Path

from jam.types.base.bytes import Bytes
from jam.types.extrinsics.preimages import Preimage, PreimagesExtrinsic
from jam.types.protocol.core import ServiceId

def test_preimages_extrinsic_encoding():
    """Test encoding/decoding of PreimagesExtrinsic against test vectors."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "preimages_extrinsic.json", "r") as f:
        preimages_json = json.load(f)
    
    with open(test_dir / "preimages_extrinsic.bin", "rb") as f:
        expected_bytes = f.read()

    # Create PreimagesExtrinsic from JSON
    preimages = PreimagesExtrinsic(
        [Preimage(
            requester=ServiceId(int(p["requester"])),
            blob=Bytes(p["blob"])
        ) for p in preimages_json]
    )

    # Test encoding
    encoded = bytearray(preimages.encode_size())
    preimages.encode_into(encoded)
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = PreimagesExtrinsic.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    
    # Verify decoded matches original
    assert len(decoded) == len(preimages)
    for dec_preimage, orig_preimage in zip(decoded, preimages):
        assert dec_preimage == orig_preimage 