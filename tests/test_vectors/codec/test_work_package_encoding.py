"""Tests for work package encoding."""
import json
from pathlib import Path

from jam.types.base.integers import U16, U32
from jam.types.base.vector import Vector
from jam.types.protocol.crypto import BeefyRoot, HeaderHash, StateRoot
from jam.types.work import WorkPackage, WorkItem
from jam.types.base.bytes import Bytes
from jam.types.protocol.core import ServiceId, OpaqueHash, Gas, TimeSlot
from jam.types.work.item import ExtrinsicSpec, ImportSpec
from jam.types.work.package import Authorizer
from jam.types.work.refine_context import RefineContext

def test_work_package_encoding():
    """Test encoding/decoding of WorkPackage against test vectors."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "work_package.json", "r") as f:
        package_json = json.load(f)
    
    with open(test_dir / "work_package.bin", "rb") as f:
        expected_bytes = f.read()

    # Create WorkPackage from JSON
    package = WorkPackage(
        authorization=Bytes(bytes.fromhex(package_json["authorization"][2:])),
        auth_code_host=ServiceId(package_json["auth_code_host"]),
        authorizer=Authorizer(
            code_hash=OpaqueHash(bytes.fromhex(package_json["authorizer"]["code_hash"][2:])),
            params=Bytes(bytes.fromhex(package_json["authorizer"]["params"][2:]))
        ),
        context=RefineContext(
            anchor=HeaderHash(bytes.fromhex(package_json["context"]["anchor"][2:])),
            state_root=StateRoot(bytes.fromhex(package_json["context"]["state_root"][2:])),
            beefy_root=BeefyRoot(bytes.fromhex(package_json["context"]["beefy_root"][2:])),
            lookup_anchor=HeaderHash(bytes.fromhex(package_json["context"]["lookup_anchor"][2:])),
            lookup_anchor_slot=TimeSlot(package_json["context"]["lookup_anchor_slot"]),
            prerequisites=Vector(
                [OpaqueHash(bytes.fromhex(prerequisite[2:])) for prerequisite in package_json["context"]["prerequisites"]]
            )
        ),
        items=Vector(
            [WorkItem(
                service=ServiceId(item["service"]),
                code_hash=OpaqueHash(bytes.fromhex(item["code_hash"][2:])),
                payload=Bytes(bytes.fromhex(item["payload"][2:])),
                refine_gas_limit=Gas(item["refine_gas_limit"]),
                accumulate_gas_limit=Gas(item["accumulate_gas_limit"]),
                import_segments=Vector(
                    [ImportSpec(tree_root=OpaqueHash(bytes.fromhex(spec["tree_root"][2:])), index=U16(spec["index"])) for spec in item["import_segments"]]
                ),
                extrinsic=Vector(
                    [ExtrinsicSpec(hash=OpaqueHash(bytes.fromhex(spec["hash"][2:])), len=U32(spec["len"])) for spec in item["extrinsic"]]
                ),
                export_count=U16(item["export_count"])
            ) for item in package_json["items"]]
        )
    )

    # Test encoding
    encoded = bytearray(package.encode_size())
    package.encode_into(encoded)
    print(f"Encoded: {encoded.hex()}")
    print(f"Expected: {expected_bytes.hex()}")
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = WorkPackage.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    
    # Verify decoded matches original
    assert decoded.authorization == package.authorization
    assert decoded.auth_code_host == package.auth_code_host
    assert decoded.authorizer == package.authorizer
    assert decoded.context == package.context
    assert len(decoded.items) == len(package.items)
    for dec_item, orig_item in zip(decoded.items, package.items):
        assert dec_item == orig_item 