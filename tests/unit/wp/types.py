from tsrkit_types import structure, TypedVector

from jam.types import WorkPackage, CoreIndex, WorkReport, WorkReportHash
from jam.types.work.manifest import Extrinsics


@structure
class RefineVector:
    work_package: WorkPackage
    core_index: CoreIndex
    extrinsics: Extrinsics
    work_rep: WorkReport
    rep_hash: WorkReportHash

RefineVectors = TypedVector[RefineVector]