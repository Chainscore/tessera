from typing import Tuple

from rockstore import RockStore

from jam.models.protocol.core import ExportsRoot, ErasureRoot
from jam.models.work.manifest import Segments, ProvedSegments, SegmentIndex
from jam.models.work.shard import (
    SegmentsShard,
    SegmentShard,
    ShardIndex,
    SegShardsDict,
    SegShardDict,
)
from jam.storage.da.store import DA


class SegmentsDA(DA):
    """
    Segments DA Stores all the segments exported / imported by a node

    Key: Segments Root
    Value: Segments (Vector[Segment])
    """

    def __init__(self, db: RockStore):
        self.prefix = bytes("SEGS", "utf-8")
        self.db = db

    def put(self, root: ExportsRoot, segments: ProvedSegments) -> None:
        try:
            key = self.prefix + root.encode()
            self.db.put(key, segments.encode())
        except Exception as e:
            print("raised error", e)

    def get(self, root: ExportsRoot) -> Tuple[Segments, Segments]:
        key = self.prefix + root.encode()
        data = self.db.get(key)

        if data is None:
            raise KeyError("Segment not found in Segments DA")

        decoded_data, _ = ProvedSegments.decode_from(data)
        segment = decoded_data.segment
        proof = decoded_data.proof

        return segment, proof

    def delete(self, root: ExportsRoot) -> None:
        key = self.prefix + root.encode()
        self.db.delete(key)


class SegmentShardsDA(DA):
    """
    Segment Shards DA Stores all the segments shards built / fetched by a node

    Key: Erasure Root
    Value: Segments Shard (Vector[Segment Shard])
    """

    def __init__(self, db: RockStore):
        self.prefix = bytes("SSHRD", "utf-8")
        self.db = db

    def put_batch(self, er_root: ErasureRoot, data: SegShardsDict) -> None:
        key = self.prefix + er_root.encode()
        self.db.put(key, data.encode())

    def put_seg_shard(
        self,
        er_root: ErasureRoot,
        shard_index: ShardIndex,
        segment_index: SegmentIndex,
        shard: SegmentShard,
    ) -> None:
        key = self.prefix + er_root.encode()
        data = self.db.get(key)

        if data is None:
            ss_dict = SegShardsDict({})
        else:
            ss_dict = SegShardsDict.decode(data)

        if shard_index in ss_dict:
            s_dict = ss_dict[segment_index]
        else:
            s_dict = SegShardDict({})

        s_dict[segment_index] = shard
        ss_dict[shard_index] = s_dict
        self.db.put(key, ss_dict.encode())

    def put(self, er_root: ErasureRoot, shard_index: ShardIndex, shard: SegmentsShard) -> None:
        key = self.prefix + er_root.encode()
        data = self.db.get(key)

        if data is None:
            ss_dict = SegShardsDict({})
        else:
            ss_dict = SegShardsDict.decode(data)

        s_dict = SegShardDict({})
        for sgi, ss in enumerate(shard):
            seg_index = SegmentIndex(sgi)
            s_shard = SegmentShard(ss)

            s_dict[seg_index] = s_shard

        ss_dict[shard_index] = s_dict
        self.db.put(key, ss_dict.encode())

    def get(self, er_root: ErasureRoot) -> SegShardsDict:
        key = self.prefix + er_root.encode()
        data = self.db.get(key)

        if data is None:
            raise KeyError("Segment Shards not found in DA")

        ss_dict = SegShardsDict.decode(data)
        return ss_dict

    def delete(self, er_root: ErasureRoot) -> None:
        key = self.prefix + er_root.encode()
        self.db.delete(key)
