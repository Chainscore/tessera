"""Work report types for the JAM protocol."""

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
    # d
    digests: WorkDigests
    # g
    auth_gas_used: Uint

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
