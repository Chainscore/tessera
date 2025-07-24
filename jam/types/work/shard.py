"""Shard related types for the JAM protocol."""
from typing import List, Tuple

from tsrkit_types import Uint, Bytes, TypedVector, structure, Dictionary, TypedArray

from jam.utils.chainspec import chain_config
from jam.types.protocol.crypto import OpaqueHash
from jam.types.work.manifest import SegmentIndex

ShardIndex = Uint[16]

# Segment/s Shard/s
# SegmentShard = Bytes[SEGMENT_SIZE / chain_config.recovery_threshold] # Single Segment Shard 12 Bytes for full spec
SegmentShard = Bytes  # Single Segment Shard
SegmentsShard = TypedVector[SegmentShard]  # Vector of Segment Shard
SegmentsShards = TypedVector[
    SegmentsShard
]  # Vector of Vector of Segment Shard (Matrix)

# Segments Shard Root
SegmentsShardRoot = OpaqueHash  # Root of SegmentsShard (Vector of Segment Shard)
SegmentsShardRoots = TypedVector[SegmentsShardRoot]


# Segments Shards Storage Dictionaries
class SegShardDict(
    Dictionary[SegmentIndex, SegmentShard, "seg_index", "segment_shard"]
):
    @property
    def shard(self) -> SegmentsShard:
        s = SegmentsShard([])
        for seg_index in sorted(self):
            shard = self[seg_index]
            s.append(shard)

        return s


class SegShardsDict(
    Dictionary[ShardIndex, SegShardDict, "shard_index", "seg_shard_dict"]
):
    @property
    def shards(self) -> SegmentsShards:
        ss = SegmentsShards([])
        for shard_index in sorted(self):
            shard = self[shard_index].shard
            ss.append(shard)

        return ss

    def get_shard(self, segment_index: SegmentIndex) -> SegmentsShard:
        """returns sorted list for all the shards of a particular segment index"""
        s = SegmentsShard([])
        for shard_index in sorted(self):
            shard = self[shard_index]
            if segment_index not in shard:
                raise IndexError(
                    f"Shard with Segment Index {shard_index} and Shard Index {segment_index} not present."
                )
            seg_shard = shard[segment_index]
            s.append(seg_shard)

        return s

    def get_shard_tuple(
        self, segment_index: SegmentIndex, sort=False
    ) -> List[Tuple[SegmentShard, ShardIndex]]:
        """returns list for all the shards of a particular segment index as tuple"""
        s = []

        shard_dict = sorted(self) if sort else self
        for shard_index in shard_dict:
            shard = self[shard_index]
            if segment_index not in shard:
                raise IndexError(
                    f"Shard with Segment Index {shard_index} and Shard Index {segment_index} not present."
                )
            seg_shard = shard[segment_index]
            s.append((seg_shard, shard_index))

        return s


# Bundle Shard/s
BundleShard = Bytes
BundleShards = TypedVector[BundleShard]

# Bundle Shard Hash/es
BundleShardHash = OpaqueHash
BundleShardHashes = TypedVector[BundleShardHash]


# Bundle Shards Storage Dictionary
class BundleShardsDict(
    Dictionary[ShardIndex, BundleShard, "shard_index", "bundle_shard"]
):
    @property
    def shards(self) -> BundleShards:
        """returns sorted list for all the bundle shards"""
        bs = BundleShards([])
        for shard_index in sorted(self):
            shard = self[shard_index]
            bs.append(shard)

        return bs

    def get_shard_tuple(self, sort=False) -> List[Tuple[BundleShard, ShardIndex]]:
        """returns list for all the bundle shards as tuple"""
        bs = []

        shard_dict = sorted(self) if sort else self
        for shard_index in shard_dict:
            shard = self[shard_index]
            bs.append((shard, shard_index))

        return bs


# Shard key/s
@structure
class ShardKey:
    bundle_shard_hash: BundleShardHash
    segment_shard_root: SegmentsShardRoot


ShardKeys = TypedVector[ShardKey]

# Shard Keys Storage Dictionary
ShardKeysDict = Dictionary[ShardIndex, ShardKey, "shard_index", "shard_key"]


# Shard/s
@structure
class Shard:
    """clubbed shard"""

    bundle_shard: BundleShard
    segments_shard: SegmentsShard


Shards = TypedVector[Shard]
ShardsArray = TypedArray[Shard, chain_config.num_validators]
