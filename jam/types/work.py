"""Work report types for the JAM protocol."""
from typing import Tuple

from tsrkit_types.integers import Uint
from tsrkit_types.choice import Choice
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector, TypedArray
from tsrkit_types.struct import structure
from tsrkit_types.null import NullType

from jam.execution.utils import decode_code_hash
from jam.types.protocol.crypto import OpaqueHash, WorkReportHash, Hash, HeaderHash, BeefyRoot, StateRoot
from jam.types.protocol.core import (
    CoreIndex,
    SegmentRoot,
    ErasureRoot,
    ExportsRoot,
    Gas,
    ServiceId,
    WorkPackageHash, TimeSlot,
)
from jam.utils.constants import SEGMENT_SIZE


class WorkExecResult(Choice):
    """Work execution result choice."""

    ok: Bytes
    out_of_gas: NullType
    panic: NullType
    # circle dot
    bad_exports: NullType
    # BAD
    bad_code: NullType
    # BIG
    code_oversize: NullType
    # circle minus
    result_oversize: NullType


ExecResults = TypedVector[WorkExecResult]


@structure
class RefineLoad:
    """Refine load structure."""

    gas_used: Uint
    imports: Uint
    exports: Uint
    extrinsic_count: Uint
    extrinsic_size: Uint


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
class ImportSpec:
    """Import specification structure."""

    tree_root: OpaqueHash
    index: Uint[16]


@structure
class ExtrinsicSpec:
    """Extrinsic specification structure."""

    hash: OpaqueHash
    len: Uint[32]


ImportSpecs = TypedVector[ImportSpec]

ExtrinsicSpecs = TypedVector[ExtrinsicSpec]

@structure
class WorkItem:
    """Work item structure."""
    # s
    service: ServiceId
    # h
    code_hash: OpaqueHash
    # y
    payload: Bytes
    # g
    refine_gas_limit: Gas
    # a
    accumulate_gas_limit: Gas
    # i
    import_segments: ImportSpecs
    # x
    extrinsic: ExtrinsicSpecs
    # e
    export_count: Uint[16]


WorkResults = TypedVector[WorkResult]




@structure
class RefineContext:
    """Refine context structure."""

    anchor: HeaderHash
    state_root: StateRoot
    beefy_root: BeefyRoot
    lookup_anchor: HeaderHash
    lookup_anchor_slot: TimeSlot
    prerequisites: TypedVector[OpaqueHash]

    @staticmethod
    def empty() -> "RefineContext":
        return RefineContext(
            anchor=HeaderHash([0]*32),
            state_root=StateRoot([0]*32),
            beefy_root=BeefyRoot([0]*32),
            lookup_anchor=HeaderHash([0]*32),
            lookup_anchor_slot=TimeSlot(0),
            prerequisites=TypedVector[OpaqueHash]([]),
        )

SegmentRootLookup = Dictionary[WorkPackageHash, SegmentRoot]


@structure
class WorkReport:
    """Work report structure."""
    # s
    package_spec: WorkPackageSpec
    # x
    context: RefineContext
    # c
    core_index: Uint
    # a
    authorizer_hash: OpaqueHash
    # o
    auth_output: Bytes
    # l
    segment_root_lookup: SegmentRootLookup
    # r
    results: WorkResults
    # g
    auth_gas_used: Uint

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

@structure
class Authorizer:
    """Authorizer structure."""
    # u
    code_hash: OpaqueHash
    # p
    params: Bytes

    def __hash__(self) -> int:
        return Hash.blake2b(bytes(self.code_hash) + bytes(self.params))


WorkItems = TypedVector[WorkItem]


@structure
class WorkPackage:
    """Work package structure."""
    # j
    authorization: Bytes
    # h
    auth_code_host: ServiceId
    # u, p
    authorizer: Authorizer
    # x
    context: RefineContext
    # w
    items: WorkItems

    def m_c(self, delta: "Delta") -> Tuple[bytes, bytes]:
        service_data = delta[self.auth_code_host].historical_lookup(self.context.lookup_anchor_slot, self.authorizer.code_hash)
        return decode_code_hash(service_data)




Segment = TypedArray[int, SEGMENT_SIZE]

Segments = TypedVector[Segment]

MultiSegments = TypedVector[Segments]



@structure
class WorkPackageBundle:
    """Work package bundle specification structure."""

    package: WorkPackage
    extrinsics: TypedVector[TypedVector[Bytes]]
    import_segments: TypedVector[MultiSegments]
    justifications: TypedVector[TypedVector[TypedVector[OpaqueHash]]]

