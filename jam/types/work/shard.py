"""Shard related types for the JAM protocol."""

from tsrkit_types import Uint, Bytes, TypedVector, structure

from jam.types.protocol.crypto import OpaqueHash

ShardIndex = Uint[16]
SegmentShard = Bytes
SegmentsShardRoot = OpaqueHash
BundleShard = Bytes
BundleShardHash = OpaqueHash

SegmentsShardRoots = TypedVector[SegmentsShardRoot]
BundleShardHashes = TypedVector[BundleShardHash]

SegmentsShard = TypedVector[SegmentShard]
SegmentsShards = TypedVector[SegmentsShard]

BundleShards = TypedVector[BundleShard]

@structure
class SegmentsShardUnit:
    """contains segments shard ( Vector of 12 byte segment shard )"""

    shard_index: ShardIndex
    shard: SegmentsShard

@structure
class BundleShardUnit:
    """contains bundle shard"""

    shard_index: ShardIndex
    shard: BundleShard

@structure
class ShardKey:
    """contains shard key pairs"""

    bundle_shard_hash: BundleShardHash
    segment_shard_root: SegmentsShardRoot

ShardKeys = TypedVector[ShardKey]

@structure
class ShardKeyUnit:
    """contains shard key pairs"""

    shard_index: ShardIndex
    bundle_shard_hash: BundleShardHash
    segment_shard_root: SegmentsShardRoot

ShardKeyUnits = TypedVector[ShardKeyUnit]

@structure
class SSKeysUnit:
    """contains segments shard root"""

    shard_index: ShardIndex
    segment_shard_root: SegmentsShardRoot

SSKeysUnits = TypedVector[SSKeysUnit]

@structure
class BSKeysUnit:
    """contains bundle shard hash"""

    shard_index: ShardIndex
    bundle_shard_hash: BundleShardHash

BSKeysUnits = TypedVector[BSKeysUnit]

@structure
class Shard:
    """contains clubbed shard"""

    bundle_shard: BundleShard
    segment_shard: SegmentShard

Shards = TypedVector[Shard]