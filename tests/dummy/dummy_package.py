from jam.network.protocols.ce_134 import WorkPackageBundle, CoreSegment, Credential
from jam.types import  U32, Bytes, Int
from jam.types.work.package import WorkItems, OpaqueHash, WorkPackage, Authorizer
from jam.types.work.report import SegmentRootLookup
from jam.types.work.segment import Segments

from tests.dummy.dummy_extrinsics import create_dummy_work_context
from tests.dummy.utils import create_dummy_bytes, create_dummy_bytes32
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
        code_hash=OpaqueHash(create_dummy_bytes32()),
        params=Bytes(create_dummy_bytes(10)),
        context=create_dummy_work_context(),
        items=WorkItems([])
    )

def create_dummy_bundle() -> WorkPackageBundle :
    """create dummy work package bundle"""
    return WorkPackageBundle (
        workPackage=create_dummy_package,
        extrinsic=OpaqueHash(create_dummy_bytes32()),
        import_segment= Segments([])
    )

def crete_dummy_coreSegment() -> CoreSegment:

    segment_root_map = SegmentRootLookup({})
    work_package_hash = OpaqueHash(create_dummy_bytes32()),
    segment = OpaqueHash(create_dummy_bytes32()),

    segment_root_map[work_package_hash] = segment

    return CoreSegment (
        core_index=Int(0),
        length=Int(1),
        segment_root_map=segment_root_map
    )

def create_dummy_Credential() -> Credential:
    return Credential (
        workreportHash=OpaqueHash(create_dummy_bytes32()),
        ed25519signature=OpaqueHash(create_dummy_bytes32())
    )



