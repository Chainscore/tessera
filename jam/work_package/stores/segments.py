from typing import Tuple

from jam.db.kv import KVStore
from jam.types.protocol.core import ExportsRoot
from jam.types.work.manifest import Segments, ProvedSegments
from jam.types.work.shard import SegmentsShardRoot, SegmentsShardUnit, SegmentsShard, ShardIndex, SegmentsShardRoots
from jam.work_package.store import DA


class SegmentsDA(DA):
    """
    Segments DA Stores all the segments exported / imported by a node

    Key: Segments Root
    Value: Segments (Vector[Segment])
    """

    def __init__(self, db: KVStore):
        self.prefix = bytes("SEG", 'utf-8')
        self.db = db

    def put(self, root: ExportsRoot, segments: ProvedSegments) -> None:
        key = self.prefix + root.encode()
        self.db.put(key, segments.encode())

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

    Key: Segments Shard Root
    Value: Segments Shard (Vector[Segment Shard])
    """

    def __init__(self, db: KVStore):
        self.prefix = bytes("SS", 'utf-8')
        self.db = db

    def put(self, root: SegmentsShardRoot, data: SegmentsShardUnit) -> None:
        key = self.prefix + root.encode()
        self.db.put(key, data.encode())

    def get(self, root: SegmentsShardRoot) -> Tuple[SegmentsShard, ShardIndex]:
        key = self.prefix + root.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Segment Shards not found in DA")

        record, _ = SegmentsShardUnit.decode_from(data)

        return record.shard, record.shard_index

    def delete(self, root: SegmentsShardRoot) -> None:
        key = self.prefix + root.encode()
        self.db.delete(key)
