from jam.types import WorkPackage, Authorizer, OpaqueHash, U32, Bytes
from jam.types.work.package import WorkItems
from tests.fixtures.dummy_extrinsics import create_dummy_work_context
from tests.fixtures.utils import create_dummy_Bytes, create_dummy_bytes32

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
        code_hash=OpaqueHash(create_dummy_bytes32()),
        params=create_dummy_Bytes(10),
        context=create_dummy_work_context(),
        items=WorkItems([])
    )

