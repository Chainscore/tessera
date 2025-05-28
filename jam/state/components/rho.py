import random
from dataclasses import dataclass
from jam.types import Option, Null, WorkPackageSpec, U32, U16, Dictionary, WorkResult, WorkExecResult, U64, U8, \
    RefineContext
from jam.types.base import Choice
from jam.types.base.choices.option import decodable_option
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.protocol.core import TimeSlot
from jam.types.work.refine_context import OpaqueHashes
from jam.types.work.report import WorkReport, WorkResults, RefineLoad
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.constants import CORE_COUNT
from jam.types.base.choices.option import Option
from jam.utils.json import JsonSerde




@decodable_dataclass
@dataclass
class WorkReportState(Codable, JsonSerde):
    """Work report state"""

    report: WorkReport
    timeout: TimeSlot


@decodable_option(WorkReportState)
class OptionalWorkReportState(Option):
    """Work report state"""
    ...


@decodable_array(CORE_COUNT, OptionalWorkReportState)
class Rho(Array[OptionalWorkReportState]):
    """Work report state array"""




pending = Rho([OptionalWorkReportState(Null), OptionalWorkReportState(WorkReportState(report=WorkReport(package_spec=WorkPackageSpec(hash=0xfe0c43b1fdd676185b192c3f496bfc42de4cb1f507cb91c7b7ba33de4118571d, length=U32(42), erasure_root=0xeab16881df4770bdd8ea75e1f703761b87383300f89adaad4e0908d741bc7127, exports_root=0x44e6782ffe39eb84f553298b24f5f5cb7c49fd27e7848ce3e2522acf94c0cdfc, exports_count=U16(69)), context=RefineContext(anchor=0xc7d634b5f5e5165814a43026261dcd152dfe1b90c048c8c87ff985bcb6c241b8, state_root=0x4d3676a887b68aab23e14bdb14c80fe7e534647965630b708460c3d2dc2d0727, beefy_root=0xec8d658d168092abffe0156c3efd391fda2b50b9e3640c0bb39fead27ab5730e, lookup_anchor=0xefd88ab9b4ed95133ebeecb8629678136ded30de6a95ef9ab61107fd843dbaf5, lookup_anchor_slot=U32(33), prerequisites=OpaqueHashes([])), core_index=U16(3), authorizer_hash=0xb3a5f0e7c2c3c32e681ef8ddc9fe71a460a163d24ce441eb586df50580304057, auth_output=0x0102030405, segment_root_lookup=Dictionary({}), results=WorkResults([WorkResult(service_id=U32(16909060), code_hash=0x2335ddcc85f7a2bd8ba13af4c0d21daf439218cf4f64a4893885cc23b3a6dd04, payload_hash=0x87dc3f01d7bb5fe944edf755cc66e2b85c7692482fc9434a4c99cde07a763a30, accumulate_gas=U64(42), result=WorkExecResult({'ok': 0xbb55ae8daced9d5688e8e8bb5c5b87b6}), refine_load=RefineLoad(gas_used=U64(0), imports=U16(0), exports=U16(0), extrinsic_count=U8(0), extrinsic_size=U64(0)))]), auth_gas_used=U64(0)), timeout=U32(0)))])
print(pending[0])


def generate_random_work_report_state() -> OptionalWorkReportState:
    from tests.dummy.dummy_extrinsics import create_dummy_work_report

    choice = random.randint(0, 1)
    if choice == 0:
        return OptionalWorkReportState(Null)

    # Generate dummy data
    report = create_dummy_work_report()

    timeslot = TimeSlot(0)

    state = WorkReportState(report=report, timeout=timeslot)
    return OptionalWorkReportState(state)

#
def create_dummy_rho() -> Rho:
    return Rho([generate_random_work_report_state() for i in range(CORE_COUNT)])


# print(create_dummy_rho())