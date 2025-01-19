"""Tests for work item encoding."""
import json
from pathlib import Path

from jam.types.base import Vector
from jam.types.work import WorkItem
from jam.types.base import Bytes
from jam.types.base.integers import U16, U32
from jam.types.protocol.core import ServiceId, OpaqueHash, Gas
from jam.types.work.item import ExtrinsicSpec, ImportSpec

def test_work_item_encoding():
    """Test encoding/decoding of WorkItem against test vectors."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "work_item.json", "r") as f:
        item_json = json.load(f)
    
    with open(test_dir / "work_item.bin", "rb") as f:
        expected_bytes = f.read()

    # Create WorkItem from JSON
    item = WorkItem(
        service=ServiceId(item_json["service"]),
        code_hash=OpaqueHash(bytes.fromhex(item_json["code_hash"][2:])),
        payload=Bytes(bytes.fromhex(item_json["payload"][2:])),
        refine_gas_limit=Gas(item_json["refine_gas_limit"]),
        accumulate_gas_limit=Gas(item_json["accumulate_gas_limit"]),
        import_segments=Vector(
            [ImportSpec(tree_root=OpaqueHash(bytes.fromhex(spec["tree_root"][2:])), index=U16(spec["index"])) for spec in item_json["import_segments"]]
        ),
        extrinsic=Vector(
            [ExtrinsicSpec(hash=OpaqueHash(bytes.fromhex(spec["hash"][2:])), len=U32(spec["len"])) for spec in item_json["extrinsic"]]
        ),
        export_count=U16(item_json["export_count"])
    )

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