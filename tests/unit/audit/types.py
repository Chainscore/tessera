from tsrkit_types import structure, TypedVector

from jam.block.block import Block
from jam.state.state import State
from jam.models.work.report import WorkReports


@structure
class AuditVector:
    block: Block
    reports: WorkReports
    pre_state: State
    post_state: State

AuditVectors = TypedVector[AuditVector]
