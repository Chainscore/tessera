from jam.types.work.report import WorkReport, WorkPackageSpec
from jam.types import WorkPackage, Authorizer, OpaqueHash, U32, Bytes, U16
from jam.types.work.package import WorkItems
from tests.fixtures.dummy_extrinsics import create_dummy_work_context
from tests.fixtures.utils import create_dummy_Bytes, create_dummy_bytes32
from jam.types.work.refine_context import RefineContext, OpaqueHashes
from typing import Any
from jam.types.protocol.core import Gas
from jam.work_package.work_package import SegmentRootLookupDict
from jam.types.base.dictionary import decodable_dictionary, Dict
from tests.fixtures.dummy_work_result import create_dummy_work_results

def create_dummy_report() -> WorkReport:
    specs = WorkPackageSpec(
        hash=OpaqueHash(create_dummy_bytes32()),
        length=U32(12),
        erasure_root= OpaqueHash(create_dummy_bytes32()),
        exports_root= OpaqueHash(create_dummy_bytes32()),
        exports_count= U16(10)
    )

    segment_lookup = SegmentRootLookupDict(Dict(OpaqueHash(create_dummy_bytes32()), OpaqueHash(create_dummy_bytes32())))

    return WorkReport(
        package_spec= specs,
        context= create_dummy_work_context(),
        core_index= U16(1),
        authorizer_hash=OpaqueHash(create_dummy_bytes32()),
        auth_output=Bytes(create_dummy_Bytes(20)),
        auth_gas_used= Gas(10),
        segment_root_lookup= segment_lookup,
        results= create_dummy_work_results()
    )