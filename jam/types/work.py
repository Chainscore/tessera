"""Work package and work report types for the JAM protocol."""
from dataclasses import dataclass
from typing import List, Optional, Union
from .base import ByteSequence, U16, U32
from .core import (
    OpaqueHash, HeaderHash, StateRoot, BeefyRoot, Gas, ServiceId,
    WorkPackageHash, WorkReportHash, ExportsRoot, ErasureRoot, CoreIndex
)

@dataclass
class ImportSpec:
    """Import specification structure."""
    tree_root: OpaqueHash
    index: U16

@dataclass
class ExtrinsicSpec:
    """Extrinsic specification structure."""
    hash: OpaqueHash
    len: U32

@dataclass
class Authorizer:
    """Authorizer structure."""
    code_hash: OpaqueHash
    params: ByteSequence

@dataclass
class RefineContext:
    """Refine context structure."""
    anchor: HeaderHash
    state_root: StateRoot
    beefy_root: BeefyRoot
    lookup_anchor: HeaderHash
    lookup_anchor_slot: U32
    prerequisites: List[OpaqueHash]

@dataclass
class WorkItem:
    """Work item structure."""
    service: ServiceId
    code_hash: OpaqueHash
    payload: ByteSequence
    refine_gas_limit: Gas
    accumulate_gas_limit: Gas
    import_segments: List[ImportSpec]
    extrinsic: List[ExtrinsicSpec]
    export_count: U16

@dataclass
class WorkPackage:
    """Work package structure."""
    authorization: ByteSequence
    auth_code_host: ServiceId
    authorizer: Authorizer
    context: RefineContext
    items: List[WorkItem]

    def __post_init__(self):
        if not 1 <= len(self.items) <= 4:
            raise ValueError("WorkPackage must contain between 1 and 4 work items")

@dataclass
class WorkExecResult:
    """Work execution result."""
    result: Union[ByteSequence, str]  # 'out-of-gas', 'panic', 'bad-code', 'code-oversize'
    is_ok: bool = True

    @classmethod
    def ok(cls, value: ByteSequence) -> 'WorkExecResult':
        return cls(result=value, is_ok=True)

    @classmethod
    def error(cls, error_type: str) -> 'WorkExecResult':
        if error_type not in ['out-of-gas', 'panic', 'bad-code', 'code-oversize']:
            raise ValueError(f"Invalid error type: {error_type}")
        return cls(result=error_type, is_ok=False)

@dataclass
class WorkResult:
    """Work result structure."""
    service_id: ServiceId
    code_hash: OpaqueHash
    payload_hash: OpaqueHash
    accumulate_gas: Gas
    result: WorkExecResult

@dataclass
class WorkPackageSpec:
    """Work package specification structure."""
    hash: WorkPackageHash
    length: U32
    erasure_root: ErasureRoot
    exports_root: ExportsRoot
    exports_count: U16

@dataclass
class SegmentRootLookupItem:
    """Segment root lookup item structure."""
    work_package_hash: WorkPackageHash
    segment_tree_root: OpaqueHash

@dataclass
class WorkReport:
    """Work report structure."""
    package_spec: WorkPackageSpec
    context: RefineContext
    core_index: CoreIndex
    authorizer_hash: OpaqueHash
    auth_output: ByteSequence
    segment_root_lookup: List[SegmentRootLookupItem]
    results: List[WorkResult]

    def __post_init__(self):
        if not 1 <= len(self.results) <= 4:
            raise ValueError("WorkReport must contain between 1 and 4 work results") 