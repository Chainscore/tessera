"""Tests for work report encoding."""
import json
from pathlib import Path
from jam.types.work import WorkReport

def test_work_report_encoding():
    """Test encoding/decoding of WorkReport against test vectors."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "work_report.json", "r") as f:
        report_json = json.load(f)
    
    with open(test_dir / "work_report.bin", "rb") as f:
        expected_bytes = f.read()

    # Create WorkReport from JSON
    report = WorkReport.from_json(report_json)

    # Test encoding
    encoded = bytearray(report.encode_size())
    report.encode_into(encoded)
    assert bytes(encoded) == expected_bytes

    # # Test decoding
    decoded, size = WorkReport.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    
    # Verify decoded matches original
    assert decoded.package_spec == report.package_spec
    assert decoded.context == report.context
    assert decoded.core_index == report.core_index
    assert decoded.authorizer_hash == report.authorizer_hash
    assert decoded.auth_output == report.auth_output
    assert len(decoded.segment_root_lookup) == len(report.segment_root_lookup)
    for dec_item, orig_item in zip(decoded.segment_root_lookup, report.segment_root_lookup):
        assert dec_item == orig_item
    assert len(decoded.results) == len(report.results)
    for dec_result, orig_result in zip(decoded.results, report.results):
        assert dec_result.result == orig_result.result