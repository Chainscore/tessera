"""Shard related types for the JAM protocol."""

from dataclasses import dataclass

from jam.types.base.integers import U16
from jam.types.base.sequences.bytes import Bytes, ByteArray12
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import OpaqueHash

from jam.utils.json.serde import JsonSerde
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass

ShardIndex = U16
SegmentShard = Bytes
SegmentsShardRoot = OpaqueHash
BundleShard = Bytes
BundleShardHash = OpaqueHash

@decodable_vector(element_type=SegmentsShardRoot)
class SegmentsShardRoots(Vector[SegmentsShardRoot]):
    ...

@decodable_vector(element_type=BundleShardHash)
class BundleShardHashes(Vector[BundleShardHash]):
    ...

@decodable_dataclass
@dataclass
class SegmentsShardTuple(Codable, JsonSerde):
    segment_shard_index: ShardIndex
    shard: SegmentShard

@decodable_vector(element_type=SegmentsShardTuple)
class SegmentsShard(Vector[SegmentsShardTuple]):
    ...

# @decodable_vector(element_type=SegmentShard)
# class SegmentsShard(Vector[SegmentShard]):
#     ...

# @decodable_vector(element_type=SegmentsShard)
# class SegmentsShards(Vector[SegmentsShard]):
#     ...

@decodable_vector(element_type=SegmentsShard)
class SegmentsShards(Vector[SegmentsShard]):
    ...

@decodable_vector(element_type=BundleShard)
class BundleShards(Vector[BundleShard]):
    ...

@decodable_dataclass
@dataclass
class SegmentsShardUnit(Codable, JsonSerde):
    """contains segments shard ( Vector of 12 byte segment shard )"""
    shard_index: ShardIndex
    shard: SegmentsShard

@decodable_dataclass
@dataclass
class BundleShardUnit(Codable, JsonSerde):
    """contains bundle shard"""
    shard_index: ShardIndex
    shard: BundleShard

@decodable_dataclass
@dataclass
class ShardKey(Codable, JsonSerde):
    """contains shard key pairs"""
    bundle_shard_hash: BundleShardHash
    segment_shard_root: SegmentsShardRoot

@decodable_dataclass
@dataclass
class ShardKeyUnit(Codable, JsonSerde):
    """contains shard key pairs"""
    shard_index: ShardIndex
    bundle_shard_hash: BundleShardHash
    segment_shard_root: SegmentsShardRoot

@decodable_vector(element_type=ShardKey)
class ShardKeys(Vector[ShardKey]):
    ...

@decodable_vector(element_type=ShardKeyUnit)
class ShardKeyUnits(Vector[ShardKeyUnit]):
    ...

@decodable_dataclass
@dataclass
class SSKeysUnit(Codable, JsonSerde):
    """contains segments shard root"""
    shard_index: ShardIndex
    segment_shard_root: SegmentsShardRoot

@decodable_vector(element_type=SSKeysUnit)
class SSKeysUnits(Vector[SSKeysUnit]):
    ...

@decodable_dataclass
@dataclass
class BSKeysUnit(Codable, JsonSerde):
    """contains bundle shard hash"""
    shard_index: ShardIndex
    bundle_shard_hash: BundleShardHash

@decodable_vector(element_type=BSKeysUnit)
class BSKeysUnits(Vector[BSKeysUnit]):
    ...

@decodable_dataclass
@dataclass
class Shard(Codable, JsonSerde):
    """contains clubbed shard"""
    bundle_shard: BundleShard
    segment_shard: SegmentShard

@decodable_vector(element_type=Shard)
class Shards(Vector[Shard]):
    ...