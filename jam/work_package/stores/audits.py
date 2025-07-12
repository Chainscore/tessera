from typing import Tuple

from rockstore import RockStore
from tsrkit_types import TypedVector

from jam.types import OpaqueHash
from jam.types.protocol.core import ErasureRoot
from jam.types.work.shard import BundleShard, ShardIndex, BundleShardsDict

from jam.work_package.store import DA


class JustificationsDA(DA):
    """
    Justifications DA Stores all the justifications received via CE137

    Key: Erasure Root
    Value: Vector of hashes
    """

    def __init__(self, db: RockStore):
        self.prefix = bytes("JUST", "utf-8")
        self.db = db

    def put(self, er_root: ErasureRoot, data: TypedVector[OpaqueHash]) -> None:
        key = self.prefix + er_root.encode()
        self.db.put(key, data.encode())

    def get(self, er_root: ErasureRoot) -> TypedVector[OpaqueHash]:
        key = self.prefix + er_root.encode()
        data = self.db.get(key)

        if data is None:
            raise KeyError("CE137 Justification not found in Audit DA")

        record, _ = TypedVector[OpaqueHash].decode_from(data)
        return record

    def delete(self, er_root: ErasureRoot) -> None:
        key = self.prefix + er_root.encode()
        self.db.delete(key)


class AuditShardsDA(DA):
    """
    Audit Shards DA Stores all the bundle shards built / fetched by a node

    Key: Bundle Shard Hash
    Value: Bundle Shard (Bytes)
    """

    def __init__(self, db: RockStore):
        self.prefix = bytes("BSHRD", "utf-8")
        self.db = db

    def put_batch(self, er_root: ErasureRoot, data: BundleShardsDict) -> None:
        key = self.prefix + er_root.encode()
        self.db.put(key, data.encode())

    def put(
        self, er_root: ErasureRoot, shard_index: ShardIndex, shard: BundleShard
    ) -> None:
        key = self.prefix + er_root.encode()
        data = self.db.get(key)

        if data is None:
            bs_dict = BundleShardsDict({})
        else:
            bs_dict = BundleShardsDict.decode(data)

        bs_dict[shard_index] = shard
        self.db.put(key, bs_dict.encode())

    def get(self, er_root: ErasureRoot) -> BundleShardsDict:
        key = self.prefix + er_root.encode()
        data = self.db.get(key)

        if data is None:
            raise KeyError("Bundle Shard not found in Audit DA")

        bs_dict = BundleShardsDict.decode(data)
        return bs_dict

    def delete(self, er_root: ErasureRoot) -> None:
        key = self.prefix + er_root.encode()
        self.db.delete(key)
