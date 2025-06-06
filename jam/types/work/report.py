"""Work report types for the JAM protocol."""

from typing import TYPE_CHECKING

from tsrkit_types.integers import Uint
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.types.protocol.core import CoreIndex, Gas, TimeSlot
from jam.types.protocol.crypto import (
    OpaqueHash,
    WorkReportHash,
    HeaderHash,
    BeefyRoot,
    StateRoot,
)

if TYPE_CHECKING:
    from jam.types.work.package import WorkPackageSpec
    from jam.types.work.segments import SegmentRootLookup
    from jam.types.work.collections import WorkResults


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


@structure
class WorkReport:
    """Work report structure."""
    # s
    package_spec: "WorkPackageSpec"
    # x
    context: RefineContext
    # c
    core_index: Uint
    # a
    authorizer_hash: OpaqueHash
    # o
    auth_output: Bytes
    # l
    segment_root_lookup: "SegmentRootLookup"
    # r
    results: "WorkResults"
    # g
    auth_gas_used: Uint

    @classmethod
    def empty(cls, **overrides) -> "WorkReport":
        from jam.types.work.package import WorkPackageSpec
        from jam.types.work.segments import SegmentRootLookup
        from jam.types.work.collections import WorkResults
        
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