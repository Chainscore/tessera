from typing import Tuple

from jam.storage.db.kv import KVStore
from jam.types.work.shard import BundleShardHash, BundleShardUnit, BundleShard, ShardIndex

from jam.work_package.store import DA

class JustificationsDA(DA):
    ...


class AuditShardsDA(DA):
    """
    Audit Shards DA Stores all the bundle shards built / fetched by a node

    Key: Bundle Shard Hash
    Value: Bundle Shard (Bytes)
    """

    def __init__(self, db: KVStore):
        self.prefix = bytes("BS", 'utf-8')
        self.db = db

    def put(self, bs_hash: BundleShardHash, data: BundleShardUnit) -> None:
        key = self.prefix + bs_hash.encode()
        self.db.put(key, data.encode())

    def get(self, bs_hash: BundleShardHash) -> Tuple[BundleShard, ShardIndex]:
        key = self.prefix + bs_hash.encode()
        data = self.db.get(key)

        if data is None:
            raise KeyError("Bundle Shard not found in Audit DA")

        record, _ = BundleShardUnit.decode_from(data)
        return record.shard, record.shard_index

    def delete(self, bs_hash: BundleShardHash) -> None:
        key = self.prefix + bs_hash.encode()
        self.db.delete(key)