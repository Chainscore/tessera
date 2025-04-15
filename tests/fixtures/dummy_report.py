from jam.types.work.report import WorkReport, WorkPackageSpec
from jam.types import WorkPackage, Authorizer, OpaqueHash, U32, Bytes, U16
from jam.types.work.package import WorkItems
from tests.fixtures.dummy_extrinsics import create_dummy_work_context
from tests.fixtures.utils import create_dummy_Bytes, create_dummy_bytes32
from jam.types.work.refine_context import RefineContext, OpaqueHashes
from typing import Any


def create_dummy_report() -> WorkReport:
    specs = WorkPackageSpec(
        hash=OpaqueHash(create_dummy_bytes32()),
        length=U32(12),
        erasure_root= OpaqueHash(create_dummy_bytes32()),
        exports_root= OpaqueHash(create_dummy_bytes32()),
        exports_count= U16(10)
    )

    return WorkReport(
        package_spec= specs,
        context= create_dummy_work_context(),
        core_index= U16(1),
        authorizer_hash=OpaqueHash(create_dummy_bytes32()),
        auth_output=Bytes(create_dummy_Bytes(20)),
        segment_root_lookup= Any,
        results= Any
    )