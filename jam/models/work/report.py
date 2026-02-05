"""Work report types for the JAM protocol."""
from dataclasses import field

from tsrkit_types.integers import Uint
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.types.protocol.core import CoreIndex, Gas
from jam.types.protocol.crypto import (
    OpaqueHash,
    WorkReportHash, Hash
)
from jam.types.work.execution import WorkDigests, RefineContext
from jam.types.work.package import WorkPackageSpec
from jam.types.work.manifest import SegmentRootLookup


@structure
class WorkReport:
    """
    Set R
    Work report structure.

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/133f02133f02?v=0.7.0
    """

    # s
    package_spec: WorkPackageSpec
    # bold c
    context: RefineContext
    # c
    core_index: Uint
    # a
    authorizer_hash: OpaqueHash
    # g
    auth_gas_used: Uint
    # bold t
    auth_output: Bytes
    # bold l
    segment_root_lookup: SegmentRootLookup
    # bold d
    digests: WorkDigests = field(metadata={"name": "results"})

    def hash(self) -> WorkReportHash:
        return WorkReportHash(Hash.blake2b(self.encode()))

    @classmethod
    def empty(cls, **overrides) -> "WorkReport":
        from jam.types.work.package import WorkPackageSpec
        from jam.types.work.manifest import SegmentRootLookup
        from jam.types.work import WorkDigests
        
        defaults = {
            "package_spec": WorkPackageSpec.empty(),
            "context": RefineContext.empty(),
            "core_index": CoreIndex(0),
            "authorizer_hash": OpaqueHash(bytes([0] * 32)),
            "auth_output": Bytes(b""),
            "segment_root_lookup": SegmentRootLookup({}),
            "digests": WorkDigests([]),
            "auth_gas_used": Gas(0),
        }
        # merge in anything the caller wants to override:
        defaults.update(overrides)
        return cls(**defaults)


WorkDependencies = TypedVector[WorkReportHash]  # Set of dependencies hashes

WorkReports = TypedVector[WorkReport]  # Vector of Work Reports
