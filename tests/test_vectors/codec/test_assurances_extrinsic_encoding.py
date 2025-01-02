"""Tests for assurances extrinsic encoding."""
import json
from pathlib import Path

from jam.types.base.vector import Vector
from jam.types.extrinsics.assurances import AssurancesExtrinsic, AvailAssurance, AvailBitField
from jam.types.protocol.core import ValidatorIndex
from jam.types.protocol.crypto import Ed25519Signature, OpaqueHash

def test_assurances_extrinsic_encoding():
    """Test encoding/decoding of AssurancesExtrinsic against test vectors."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "assurances_extrinsic.json", "r") as f:
        assurances_json = json.load(f)
    
    with open(test_dir / "assurances_extrinsic.bin", "rb") as f:
        expected_bytes = f.read()

    # Create AssurancesExtrinsic from JSON
    assurances = AssurancesExtrinsic(
        [AvailAssurance(
            anchor=OpaqueHash(a["anchor"][2:]),
            bitfield=AvailBitField(a["bitfield"]),
            validator_index=ValidatorIndex(a["validator_index"]),
            signature=Ed25519Signature(a["signature"])
        ) for a in assurances_json]
    )

    # Test encoding
    encoded = bytearray(assurances.encode_size())
    assurances.encode_into(encoded)
    assert bytes(encoded) == expected_bytes

    # # Test decoding
    decoded, size = AssurancesExtrinsic.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    assert decoded == assurances
