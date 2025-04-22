from jam.types import WorkPackage, Authorizer, OpaqueHash, U32, Bytes, ByteArray32, decodable_vector
from jam.types.work.package import WorkItems
from tests.fixtures.dummy_extrinsics import create_dummy_work_context
from tests.fixtures.utils import create_dummy_Bytes, create_dummy_bytes32
from jam.network.protocols.ce_134 import Credential, WorkPackageBundle, Segments, CoreSegment
from jam.work_package.work_package import SegmentRootLookupDict

def create_dummy_authorizer() -> Authorizer:
    return Authorizer(
        code_hash=OpaqueHash(create_dummy_bytes32()),
        params=Bytes(create_dummy_Bytes(20))
    )

def create_dummy_package() -> WorkPackage:
    """Create dummy package spec"""
    return WorkPackage(
        authorization=Bytes(create_dummy_Bytes(12)),
        auth_code_host=U32(42),
        authorizer=create_dummy_authorizer(),
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

def create_dummy_Credential() -> Credential:
    return Credential (
        workreportHash=OpaqueHash(create_dummy_bytes32()),
        ed25519signature=OpaqueHash(create_dummy_bytes32())
    )

def crete_dummy_coreSegment() -> CoreSegment:

    segment_root_map = SegmentRootLookupDict({})

    work_package_hash = OpaqueHash(create_dummy_bytes32()),

    segment = OpaqueHash(create_dummy_bytes32()),

    segment_root_map[work_package_hash] = segment

    return CoreSegment (
        core_index=0,
        segment_root_map=segment_root_map
    )


