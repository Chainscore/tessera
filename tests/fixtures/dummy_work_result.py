from jam.types.work.report import WorkResult, WorkResults
from jam.types.protocol.core import ServiceId
from tests.fixtures.dummy_extrinsics import create_dummy_work_context
from tests.fixtures.utils import create_dummy_Bytes, create_dummy_bytes32
from jam.types import WorkPackage, Authorizer, OpaqueHash, U32, Bytes, U16
from jam.types.protocol.core import Gas


def create_dummy_work_result() -> WorkResult:
    return WorkResult(
        service_id= ServiceId(10),
        code_hash=OpaqueHash(create_dummy_bytes32()),
        payload_hash= OpaqueHash(create_dummy_bytes32()),
        accumulate_gas= Gas(10),
        result=Bytes(create_dummy_Bytes(20)),
    )

def create_dummy_work_results () -> WorkResults:
    results = [create_dummy_work_result() for _ in range(5)]
    return WorkResults(results)