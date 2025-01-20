"""Tests for work item encoding."""
import json
from pathlib import Path
from jam.types.work import WorkItem

def test_work_item_encoding():
    """Test encoding/decoding of WorkItem against test vectors."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "work_item.json", "r") as f:
        item_json = json.load(f)
    
    with open(test_dir / "work_item.bin", "rb") as f:
        expected_bytes = f.read()

    # Create WorkItem from JSON
    item = WorkItem.from_json(item_json)

    # Test encoding
    encoded = bytearray(item.encode_size())
    item.encode_into(encoded)
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = WorkItem.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    
    # Verify decoded matches original
    assert decoded.service == item.service
    assert decoded.code_hash == item.code_hash
    assert decoded.payload == item.payload
    assert decoded.refine_gas_limit == item.refine_gas_limit
    assert decoded.accumulate_gas_limit == item.accumulate_gas_limit
    assert len(decoded.import_segments) == len(item.import_segments)
    for dec_spec, orig_spec in zip(decoded.import_segments, item.import_segments):
        assert dec_spec == orig_spec
    assert len(decoded.extrinsic) == len(item.extrinsic)
    for dec_spec, orig_spec in zip(decoded.extrinsic, item.extrinsic):
        assert dec_spec == orig_spec
    assert decoded.export_count == item.export_count 