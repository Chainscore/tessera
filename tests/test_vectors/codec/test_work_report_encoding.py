"""Tests for work report encoding."""
import json
from pathlib import Path

from jam.types.base.integers import U16, U32
from jam.types.base.vector import Vector
from jam.types.protocol.core import CoreIndex, ErasureRoot, ExportsRoot, Gas, ServiceId, TimeSlot
from jam.types.protocol.crypto import BeefyRoot, HeaderHash, OpaqueHash, StateRoot
from jam.types.work import WorkReport, WorkResult, WorkExecResult
from jam.types.base.bytes import Bytes
from jam.types.work.refine_context import RefineContext
from jam.types.work.report import SegmentRootLookupItem, WorkPackageSpec

def test_work_report_encoding():
    """Test encoding/decoding of WorkReport against test vectors."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "work_report.json", "r") as f:
        report_json = json.load(f)
    
    with open(test_dir / "work_report.bin", "rb") as f:
        expected_bytes = f.read()

    # Create WorkReport from JSON
    report = WorkReport(
        package_spec=WorkPackageSpec(
            hash=OpaqueHash(bytes.fromhex(report_json["package_spec"]["hash"][2:])),
            length=U32(report_json["package_spec"]["length"]),
            erasure_root=ErasureRoot(bytes.fromhex(report_json["package_spec"]["erasure_root"][2:])),
            exports_root=ExportsRoot(bytes.fromhex(report_json["package_spec"]["exports_root"][2:])),
            exports_count=U16(report_json["package_spec"]["exports_count"])
        ),
        context=RefineContext(
            anchor=HeaderHash(bytes.fromhex(report_json["context"]["anchor"][2:])),
            state_root=StateRoot(bytes.fromhex(report_json["context"]["state_root"][2:])),
            beefy_root=BeefyRoot(bytes.fromhex(report_json["context"]["beefy_root"][2:])),
            lookup_anchor=HeaderHash(bytes.fromhex(report_json["context"]["lookup_anchor"][2:])),
            lookup_anchor_slot=TimeSlot(int(report_json["context"]["lookup_anchor_slot"])),
            prerequisites=Vector(
                [OpaqueHash(bytes.fromhex(prerequisite[2:])) for prerequisite in report_json["context"]["prerequisites"]]
            )
        ),
        core_index=CoreIndex(report_json["core_index"]),
        authorizer_hash=OpaqueHash(bytes.fromhex(report_json["authorizer_hash"][2:])),
        auth_output=Bytes(bytes.fromhex(report_json["auth_output"][2:])),
        segment_root_lookup=Vector(
            [SegmentRootLookupItem(
                work_package_hash=OpaqueHash(bytes.fromhex(item["work_package_hash"][2:])),
                segment_tree_root=OpaqueHash(bytes.fromhex(item["segment_tree_root"][2:]))
            ) for item in report_json["segment_root_lookup"]]
        ),
        results=Vector(
            [WorkResult(
                service_id=ServiceId(r["service_id"]),
                code_hash=OpaqueHash(bytes.fromhex(r["code_hash"][2:])),
                payload_hash=OpaqueHash(bytes.fromhex(r["payload_hash"][2:])),
                accumulate_gas=Gas(r["accumulate_gas"]),
                result=WorkExecResult(r["result"])
            )
            for r in report_json["results"]
            ]
        )
    )

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