from rockstore import RockStore

from jam.models.protocol.core import ErasureRoot
from jam.models.work.shard import BundleShard, ShardIndex, BundleShardsDict
from jam.models.work.manifest import Justification

from jam.storage.da.store import DA



class JustificationsDA(DA):
    """
    Justifications DA Stores all the justifications received via CE137

    Key: Erasure Root
    Value: Vector of hashes
    """

    def __init__(self, db: RockStore):
        self.prefix = bytes("JUST", "utf-8")
        self.db = db

    def put(self, er_root: ErasureRoot, index: ShardIndex, data: Justification) -> None:
        key = self.prefix + er_root.encode() + index.encode()
        self.db.put(key, data.encode())

    def get(self, er_root: ErasureRoot, index: ShardIndex) -> Justification:
        key = self.prefix + er_root.encode() + index.encode()
        data = self.db.get(key)

        if data is None:
            raise KeyError("Justification not found in Audit DA")

        record, _ = Justification.decode_from(data)
        return record

    def delete(self, er_root: ErasureRoot, index: ShardIndex) -> None:
        key = self.prefix + er_root.encode() + index.encode()
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
        # Debug: print what we're storing
        if len(data) > 0:
            from jam.models.protocol.crypto import Hash
            first_key = list(data.keys())[0]
            first_hash = Hash.blake2b(data[first_key].encode()).hex()[:16]
            print(f"[AuditShardsDA] put_batch(er_root={er_root.hex()[:16]}) -> first shard hash: {first_hash}")
        self.db.put(key, data.encode())

    def put(self, er_root: ErasureRoot, shard_index: ShardIndex, shard: BundleShard) -> None:
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
            raise KeyError(f"Bundle Shard not found in Audit DA for key: {key.hex()}")

        bs_dict = BundleShardsDict.decode(data)
        # Debug: print first shard hash to verify correct data
        if len(bs_dict) > 0:
            from jam.models.protocol.crypto import Hash
            first_key = list(bs_dict.keys())[0]
            first_hash = Hash.blake2b(bs_dict[first_key].encode()).hex()[:16]
            print(f"[AuditShardsDA] get(er_root={er_root.hex()[:16]}) -> first shard hash: {first_hash}")
        return bs_dict

    def delete(self, er_root: ErasureRoot) -> None:
        key = self.prefix + er_root.encode()
        self.db.delete(key)
