"""Work report types for the JAM protocol."""

from tsrkit_types.integers import Uint
from tsrkit_types.choice import Choice
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from tsrkit_types.null import NullType
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


class WorkExecResult(Choice):
    """Work execution result choice."""

    ok: Bytes
    out_of_gas: NullType
    panic: NullType
    # circle dot
    bad_exports: NullType
    # circle minus
    result_oversize: NullType
    # BAD
    bad_code: NullType
    # BIG
    code_oversize: NullType


ExecResults = TypedVector[WorkExecResult]


@structure
class RefineLoad:
    """Refine load structure."""

    gas_used: int  # I64 equivalent - using int since Sint doesn't exist
    imports: int  # I64 equivalent
    exports: int  # I64 equivalent
    extrinsic_count: int  # I64 equivalent
    extrinsic_size: int  # I64 equivalent


@structure
class WorkResult:
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
    # x
    refine_load: RefineLoad


@structure
class WorkPackageSpec:
    """Work package specification structure."""
    # h
    hash: WorkPackageHash
    # l
    length: Uint[32]
    # u
    erasure_root: ErasureRoot
    # e
    exports_root: ExportsRoot
    # n
    exports_count: Uint[16]

    @staticmethod
    def empty():
        return WorkPackageSpec(
            hash=WorkPackageHash([0] * 32),
            length=Uint[32](0),
            erasure_root=ErasureRoot([0] * 32),
            exports_root=ExportsRoot([0] * 32),
            exports_count=Uint[16](0)
        )


@structure
class WorkPackageBundle:
    """Work package bundle specification structure."""

    package: WorkPackage
    extrinsics: TypedVector[TypedVector[Bytes]]
    import_segments: TypedVector[MultiSegments]
    justifications: TypedVector[TypedVector[TypedVector[OpaqueHash]]]


SegmentRootLookup = Dictionary[WorkPackageHash, SegmentRoot]

WorkResults = TypedVector[WorkResult]


@structure
class WorkReport:
    """Work report structure."""
    # s
    package_spec: WorkPackageSpec
    # x
    context: RefineContext
    # c
    core_index: int  # I64 equivalent - using int since Sint doesn't exist
    # a
    authorizer_hash: OpaqueHash
    # o
    auth_output: Bytes
    # l
    segment_root_lookup: SegmentRootLookup
    # r
    results: WorkResults
    # g
    auth_gas_used: int  # I64 equivalent - using int since Sint doesn't exist

    @classmethod
    def empty(cls, **overrides) -> "WorkReport":
        defaults = {
            "package_spec": WorkPackageSpec.empty(),
            "context": RefineContext.empty(),
            "core_index": CoreIndex(0),
            "authorizer_hash": OpaqueHash(bytes([0] * 32)),
            "auth_output": Bytes(b""),
            "segment_root_lookup": SegmentRootLookup({}),
            "results": WorkResults([]),
            "auth_gas_used": Gas(0),
        }
        # merge in anything the caller wants to override:
        defaults.update(overrides)
        return cls(**defaults)


WorkDependencies = TypedVector[WorkReportHash]  # Set of dependencies hashes

WorkReports = TypedVector[WorkReport]  # Vector of Work Reports
