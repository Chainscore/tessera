"""Work report types for the JAM protocol."""

from dataclasses import dataclass
from jam.types.base.null import Nullable
from jam.types.base.integers import U8, U16, U32, U64
from jam.types.base.choices.choice import Choice, decodable_choice
from jam.types.base.dictionary import decodable_dictionary, Dictionary
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.work.package import WorkPackage
from jam.types.work.refine_context import RefineContext
from jam.types.protocol.crypto import OpaqueHash, WorkReportHash
from jam.types.protocol.core import (
    CoreIndex,
    SegmentRoot,
    ErasureRoot,
    ExportsRoot,
    Gas,
    ServiceId,
    WorkPackageHash,
)
from jam.types.work.segment import MultiSegments
from jam.utils.json.serde import JsonSerde
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass



@decodable_choice
class WorkExecResult(Choice):
    """Work execution result choice."""

    ok: Bytes
    out_of_gas: Nullable
    panic: Nullable
    bad_code: Nullable
    code_oversize: Nullable
    bad_exports: Nullable


@decodable_vector(element_type=WorkExecResult)
class ExecResults(Vector[WorkExecResult]):
    ...

@decodable_dataclass
@dataclass
class RefineLoad(Codable, JsonSerde):
    """Refine load structure."""

    gas_used: Gas
    imports: U16
    exports: U16
    extrinsic_count: U8
    extrinsic_size: U64

@decodable_dataclass
@dataclass
class WorkResult(Codable, JsonSerde):
    """Work result structure."""
    # s
    service_id: ServiceId
    # h
    code_hash: OpaqueHash
    # y
    payload_hash: OpaqueHash
    # g
    accumulate_gas: Gas
    # d
    result: WorkExecResult
    refine_load: RefineLoad

@decodable_dataclass
@dataclass
class WorkPackageSpec(Codable, JsonSerde):
    """Work package specification structure."""
    # h
    hash: WorkPackageHash
    # l
    length: U32
    # u
    erasure_root: ErasureRoot
    # e
    exports_root: ExportsRoot
    # n
    exports_count: U16


@decodable_dataclass
@dataclass
class WorkPackageBundle(Codable, JsonSerde):
    """Work package bundle specification structure."""

    package: WorkPackage
    extrinsics: Vector[Vector[Bytes]]
    import_segments: Vector[MultiSegments]
    justifications: Vector[Vector[Vector[OpaqueHash]]]

# Deprecated Type
# @decodable_dataclass
# @dataclass
# class SegmentRootLookupItem(Codable, JsonSerde):
#     """Segment root lookup item structure."""
#
#     work_package_hash: WorkPackageHash
#     segment_tree_root: OpaqueHash
#
#
# @decodable_vector(SegmentRootLookupItem)
# class SegmentRootLookup(Vector[SegmentRootLookupItem]):
#     ...

@decodable_dictionary(key_type=WorkPackageHash, value_type=SegmentRoot)
class SegmentRootLookup(Dictionary[WorkPackageHash, SegmentRoot]):
    """contains all unique work-package hashes and segment root"""
    ...

@decodable_vector(WorkResult)
class WorkResults(Vector[WorkResult]): ...

@decodable_dataclass
@dataclass
class WorkReport(Codable, JsonSerde):
    """Work report structure."""
    # s
    package_spec: WorkPackageSpec
    # x
    context: RefineContext
    # c
    core_index: CoreIndex
    # a
    authorizer_hash: OpaqueHash
    # o
    auth_output: Bytes
    # l
    segment_root_lookup: SegmentRootLookup
    # r
    results: WorkResults
    # g
    auth_gas_used: Gas


@decodable_vector(element_type=WorkReportHash, allow_duplicates=False)
class WorkDependencies(Vector[WorkReportHash]):
    """Set of dependencies hashes"""

    ...


@decodable_vector(element_type=WorkReport)
class WorkReports(Vector[WorkReport]):
    """Vector of Work Reports"""

    ...


