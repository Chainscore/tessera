"""Work report types for the JAM protocol."""

from dataclasses import dataclass

from jam.types.base import Vector
from jam.types.base.choices.choice import Choice, decodable_choice
from jam.types.base.integers import U16, U32
from jam.types.base.null import Nullable
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base.sequences.vector import decodable_vector
from jam.types.protocol.core import (
    CoreIndex,
    ErasureRoot,
    ExportsRoot,
    Gas,
    ServiceId,
    WorkPackageHash,
)
from jam.types.protocol.crypto import OpaqueHash, WorkReportHash
from jam.types.work.refine_context import RefineContext
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.serde import JsonSerde


@decodable_choice
class WorkExecResult(Choice):
    """Work execution result choice."""

    ok: Bytes
    out_of_gas: Nullable
    panic: Nullable
    bad_code: Nullable
    code_oversize: Nullable

@decodable_dataclass
@dataclass
class RefineLoad(Codable, JsonSerde):
    """Refine load structure."""

    gas_used: Gas
    imports: U16
    exports: U16
    extrinsic_count: U16
    extrinsic_size: U32

@decodable_dataclass
@dataclass
class WorkResult(Codable, JsonSerde):
    """Work result structure."""

    service_id: ServiceId
    code_hash: OpaqueHash
    payload_hash: OpaqueHash
    accumulate_gas: Gas
    result: WorkExecResult
    refine_load: RefineLoad


@decodable_dataclass
@dataclass
class WorkPackageSpec(Codable, JsonSerde):
    """Work package specification structure."""

    hash: WorkPackageHash
    length: U32
    erasure_root: ErasureRoot
    exports_root: ExportsRoot
    exports_count: U16


@decodable_dataclass
@dataclass
class SegmentRootLookupItem(Codable, JsonSerde):
    """Segment root lookup item structure."""

    work_package_hash: WorkPackageHash
    segment_tree_root: OpaqueHash


@decodable_vector(SegmentRootLookupItem)
class SegmentRootLookup(Vector[SegmentRootLookupItem]): ...


@decodable_vector(WorkResult)
class WorkResults(Vector[WorkResult]): ...


@decodable_dataclass
@dataclass
class WorkReport(Codable, JsonSerde):
    """Work report structure."""

    package_spec: WorkPackageSpec
    context: RefineContext
    core_index: CoreIndex
    authorizer_hash: OpaqueHash
    auth_output: Bytes
    segment_root_lookup: SegmentRootLookup
    results: WorkResults
    auth_gas_used: Gas


@decodable_vector(element_type=WorkReportHash, allow_duplicates=False)
class WorkDependencies(Vector[WorkReportHash]):
    """Set of dependencies hashes"""

    ...


@decodable_vector(element_type=WorkReport)
class WorkReports(Vector[WorkReport]):
    """Vector of Work Reports"""

    ...
