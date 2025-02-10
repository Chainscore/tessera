"""Tests for work result encoding."""
import json
from pathlib import Path

from jam.types.work.report import WorkResult

def test_work_result_0_encoding():
    """Test encoding/decoding of WorkResult against test vector 0."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "work_result_0.json", "r") as f:
        result_json = json.load(f)
    
    with open(test_dir / "work_result_0.bin", "rb") as f:
        expected_bytes = f.read()

    # Create WorkResult from JSON
    result = WorkResult.from_json(result_json)

    print(result)

    # Test encoding
    encoded = bytearray(result.encode_size())
    result.encode_into(encoded)
    assert bytes(encoded) == expected_bytes


    # Test decoding
    decoded, size = WorkResult.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    
    # Verify decoded matches original
    assert decoded.service_id == result.service_id
    assert decoded.code_hash == result.code_hash
    assert decoded.payload_hash == result.payload_hash
    assert decoded.accumulate_gas == result.accumulate_gas
    assert decoded.result == result.result

def test_work_result_1_encoding():
    """Test encoding/decoding of WorkResult against test vector 1."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "work_result_1.json", "r") as f:
        result_json = json.load(f)
    
    with open(test_dir / "work_result_1.bin", "rb") as f:
        expected_bytes = f.read()

    # Create WorkResult from JSON
    result = WorkResult.from_json(result_json)

    # Test encoding
    encoded = bytearray(result.encode_size())
    result.encode_into(encoded)
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = WorkResult.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    
    # Verify decoded matches original
    assert decoded.service_id == result.service_id
    assert decoded.code_hash == result.code_hash
    assert decoded.payload_hash == result.payload_hash
    assert decoded.accumulate_gas == result.accumulate_gas
    assert decoded.result == result.result