from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U32, Uint
from tsrkit_types.sequences import Vector

from jam.types.protocol.core import CoreIndex
from jam.types.protocol.crypto import WorkReportHash

from jam.types.work import WorkItems, WorkPackage, Authorizer
from jam.types.protocol.crypto import OpaqueHash
from jam.types.work import SegmentRootLookup, WorkPackageBundle

from jam.network.protocols.ce_134 import CoreSegment, Credential

from jam.utils.dummy.dummy_extrinsics import create_dummy_work_context
from jam.utils.dummy.utils import create_dummy_bytes, create_dummy_bytes32, create_dummy_bytes64


def create_dummy_authorizer() -> Authorizer:
    return Authorizer(
        code_hash=OpaqueHash(create_dummy_bytes32()),
        params=Bytes(create_dummy_bytes(20))
    )

def create_dummy_package() -> WorkPackage:
    """Create dummy package spec"""

    return WorkPackage(
        authorization=Bytes(create_dummy_bytes(12)),
        auth_code_host=U32(42),
        authorizer=Authorizer(
            code_hash=OpaqueHash(create_dummy_bytes32()),
            params=Bytes(create_dummy_bytes(10)),
        ),
        context=create_dummy_work_context(),
        items=WorkItems([])
    )

def create_dummy_wp_bundle() -> WorkPackageBundle :
    """Create dummy work package bundle"""

    return WorkPackageBundle (
        package=create_dummy_package(),
        extrinsics=Vector([]),
        import_segments= Vector([]),
        justifications=Vector([])
    )

def create_dummy_core_segment() -> CoreSegment:
    """Create dummy core index and segment root lookup dictionary"""

    segment_root_map = SegmentRootLookup({})
    work_package_hash = OpaqueHash(create_dummy_bytes32()),
    segment_root = OpaqueHash(create_dummy_bytes32()),

    segment_root_map[work_package_hash] = segment_root

    return CoreSegment (
        core_index=CoreIndex(0),
        length=Uint(1),
        segment_root_map=segment_root_map
    )

def create_dummy_credential() -> Credential:
    return Credential (
        work_report_hash=WorkReportHash(create_dummy_bytes32()),
        ed25519_signature=create_dummy_bytes64()
    )



