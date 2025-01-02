"""Tests for guarantees extrinsic encoding."""
import json
from pathlib import Path

from jam.types.base.bytes import Bytes
from jam.types.base.integers import U16, U32
from jam.types.base.vector import Vector
from jam.types.extrinsics.guarantees import GuaranteesExtrinsic, ReportGuarantee, ValidatorSignature
from jam.types.protocol.core import CoreIndex, ErasureRoot, ExportsRoot, Gas, ServiceId, ValidatorIndex, TimeSlot, WorkPackageHash
from jam.types.protocol.crypto import BeefyRoot, Ed25519Signature, HeaderHash, OpaqueHash, StateRoot
from jam.types.work import WorkExecResult
from jam.types.work import WorkReport
from jam.types.work.refine_context import RefineContext
from jam.types.work.report import SegmentRootLookupItem, WorkPackageSpec, WorkResult

def test_guarantees_extrinsic_encoding():
    """Test encoding/decoding of GuaranteesExtrinsic against test vectors."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "guarantees_extrinsic.json", "r") as f:
        guarantees_json = json.load(f)
    
    with open(test_dir / "guarantees_extrinsic.bin", "rb") as f:
        expected_bytes = f.read()

    # Create GuaranteesExtrinsic from JSON
    guarantees = GuaranteesExtrinsic(
        [ReportGuarantee(
            report=WorkReport(
                package_spec=WorkPackageSpec(
                    hash=OpaqueHash(bytes.fromhex(g["report"]["package_spec"]["hash"][2:])),
                    length=U32(g["report"]["package_spec"]["length"]),
                    erasure_root=ErasureRoot(bytes.fromhex(g["report"]["package_spec"]["erasure_root"][2:])),
                    exports_root=ExportsRoot(bytes.fromhex(g["report"]["package_spec"]["exports_root"][2:])),
                    exports_count=U16(g["report"]["package_spec"]["exports_count"])
                ),
                context=RefineContext(
                    anchor=HeaderHash(g["report"]["context"]["anchor"]),
                    state_root=StateRoot(g["report"]["context"]["state_root"]),
                    beefy_root=BeefyRoot(g["report"]["context"]["beefy_root"]),
                    lookup_anchor=HeaderHash(g["report"]["context"]["lookup_anchor"]),
                    lookup_anchor_slot=TimeSlot(g["report"]["context"]["lookup_anchor_slot"]),
                    prerequisites=Vector(
                        [OpaqueHash(p) for p in g["report"]["context"]["prerequisites"]]
                    )
                ),
                core_index=CoreIndex(g["report"]["core_index"]),
                authorizer_hash=OpaqueHash(g["report"]["authorizer_hash"]),
                auth_output=Bytes(g["report"]["auth_output"]),
                segment_root_lookup=Vector([SegmentRootLookupItem(
                    work_package_hash=OpaqueHash(g["report"]["segment_root_lookup"]["work_package_hash"]),
                    segment_tree_root=OpaqueHash(g["report"]["segment_root_lookup"]["segment_tree_root"])
                ) for s in g["report"]["segment_root_lookup"]]),
                results=Vector([WorkResult(
                    service_id=ServiceId(r["service_id"]),
                    code_hash=OpaqueHash(r["code_hash"]),
                    payload_hash=OpaqueHash(r["payload_hash"]),
                    accumulate_gas=Gas(r["accumulate_gas"]),
                    result=WorkExecResult(r["result"])
                ) for r in g["report"]["results"]])
            ),
            slot=TimeSlot(g["slot"]),
            signatures=Vector(
                [ValidatorSignature(
                    validator_index=ValidatorIndex(s["validator_index"]),
                    signature=Ed25519Signature(bytes.fromhex(s["signature"][2:]))
                ) for s in g["signatures"]]
            )
        ) for g in guarantees_json])
    

    # Test encoding
    encoded = bytearray(guarantees.encode_size())
    guarantees.encode_into(encoded)
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = GuaranteesExtrinsic.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    assert decoded == guarantees
