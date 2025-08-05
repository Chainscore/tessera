from tsrkit_types import structure, TypedVector, Bytes, Vector

from jam.block import Block
from jam.state.state import State
from jam.types import (
    WorkPackage,
    CoreIndex,
    WorkReport,
    WorkReportHash,
    WorkPackageBundle,
    Segments,
)
from jam.types.work.manifest import Extrinsics, MultiSegments
from jam.types.work.shard import SegmentsShards, BundleShards, BundleShardHashes, SegmentsShardRoots


@structure
class RefineVector:
    work_package: WorkPackage
    core_index: CoreIndex
    extrinsics: Extrinsics
    work_rep: WorkReport
    rep_hash: WorkReportHash


RefineVectors = TypedVector[RefineVector]


@structure
class BundleVector:
    work_package: WorkPackage
    core_index: CoreIndex
    extrinsics: Extrinsics
    work_rep: WorkReport
    rep_hash: WorkReportHash
    bundle: WorkPackageBundle


BundleVectors = TypedVector[BundleVector]



@structure
class FullVector:
    work_package: WorkPackage
    core_index: CoreIndex
    extrinsics: Extrinsics
    work_rep: WorkReport
    rep_hash: WorkReportHash
    bundle: WorkPackageBundle
    export_segs: Segments
    import_segs: MultiSegments
    bs_hashes: BundleShardHashes
    ss_roots: SegmentsShardRoots
    seg_shards: SegmentsShards
    bun_shards: Vector[Bytes]
    shards: TypedVector[Bytes]

    def __init__(self):
        ...

FullVectors = TypedVector[FullVector]


@structure
class BlockVector:
    pre_state: State
    block: Block
    post_state: State
    vectors: FullVectors

    def __init__(self):
        ...

BlockVectors = TypedVector[BlockVector]