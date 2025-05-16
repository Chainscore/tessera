from typing import Tuple

from jam.storage.db.kv import KVStore

from jam.types.base.null import Null
from jam.types.protocol.crypto import Hash
from jam.types.protocol.core import WorkPackageHash, ExportsRoot, ErasureRoot, WorkReportHash
from jam.types.work.report import WorkReport
from jam.types.work.manifest import Assurers, ReportAssurers
from jam.types.work.shard import (
    ShardIndex,
    ShardKeyUnit,
    ShardKeyUnits,
    BSKeysUnit,
    BSKeysUnits,
    SSKeysUnit,
    SSKeysUnits,
    BundleShardHash,
    SegmentsShardRoot,
    BundleShardHashes,
    SegmentsShardRoots
)

from jam.work_package.store import DA


class PackageSegmentMap(DA):
    """
    PackageSegmentMap Maps all the packages to their segments root.

    Key: Work Package Hash
    Value: Segments Root
    """

    def __init__(self, db: KVStore):
        self.prefix = bytes("WPSR", 'utf-8')
        self.db = db

    def put(self, report: WorkReport) -> None:
        key = self.prefix + report.package_spec.hash.encode()
        data = report.package_spec.exports_root

        self.db.put(key, data.encode())

    def get(self, wp_hash: WorkPackageHash) -> ExportsRoot:
        key = self.prefix + wp_hash.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Segment Root not found in DA")

        report, _ = ExportsRoot.decode_from(data)

        return report

    def delete(self, wp_hash: WorkPackageHash) -> None:
        key = self.prefix + wp_hash.encode()
        self.db.delete(key)

class SegmentErasureMap(DA):
    """
    SegmentErasureMap Maps all the segments root to their erasure root.

    Key: Segments Root
    Value: Erasure Root
    """
    def __init__(self, db: KVStore):
        self.prefix = bytes("SRER", 'utf-8')
        self.db = db

    def put(self, root: ExportsRoot, data: ErasureRoot) -> None:
        key = self.prefix + root.encode()
        self.db.put(key, data.encode())

    def get(self, root: ExportsRoot) -> ErasureRoot:
        key = self.prefix + root.encode()
        data = self.db.get(key)

        if data is None:
            raise KeyError("Erasure Root not found in DA")

        root, _ = ErasureRoot.decode_from(data)
        return root

    def delete(self, root: ExportsRoot) -> None:
        key = self.prefix + root.encode()
        self.db.delete(key)

class ErasureAssurerMap(DA):
    """
    ErasureAssurerMap Maps all the erasure root to their work report and assurers.

    Key: Erasure Root
    Value: Work Report Hash, Assurers
    """

    def __init__(self, db: KVStore):
        self.prefix = bytes("ERWRA", 'utf-8')
        self.db = db

    def put(self, report: WorkReport, assurers: Assurers) -> None:
        report_hash = Hash.blake2b(report.encode())

        key = self.prefix + report.package_spec.erasure_root.encode()
        data = ReportAssurers(report_hash, assurers)

        self.db.put(key, data.encode())

    def get(self, root: ErasureRoot) -> Tuple[WorkReportHash, Assurers]:
        key = self.prefix + root.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Assurer & Report not found in DA")

        data, _ = ReportAssurers.decode_from(data)

        return data.report_hash, data.assurers

    def delete(self, root: ErasureRoot) -> None:
        key = self.prefix + root.encode()
        self.db.delete(key)

class ErasureShardsMap(DA):
    """
    ErasureShardsMap Maps all the erasure root to their shards (bundle shard hash, segments shard root).

    Key: Erasure Root
    Value: [(shard Index, Bundle Shard Hash, Segments Shard Root)]
    """

    def __init__(self, db: KVStore):
        self.prefix = bytes("ERSP", 'utf-8')
        self.db = db

    def put(self, root: ErasureRoot, ss_root: SegmentsShardRoot, bs_hash: BundleShardHash, shard_index: ShardIndex) -> None:
        key = self.prefix + root.encode()

        data = self.db.get(key)

        shard_key = ShardKeyUnit(shard_index, bs_hash, ss_root)

        if data is None:
            shard_keys = ShardKeyUnits([shard_key])
            self.db.put(key, shard_keys.encode())

        else:
            shard_keys, _ = ShardKeyUnits.decode_from(data)
            shard_keys.append(shard_key)
            self.db.put(key, shard_keys.encode())

    def put_batch(self, root: ErasureRoot, ss_roots: SegmentsShardRoots, bs_hashes: BundleShardHashes) -> None:
        if len(ss_roots) != 1023 or len(bs_hashes) != 1023:
            raise ValueError("Length of both batches should be 1023")

        key = self.prefix + root.encode()
        data = self.db.get(key)

        if data is not None:
            self.delete(root)

        shard_keys = ShardKeyUnits([])
        for i in range(1023):
            shard_key = ShardKeyUnit(ShardIndex(i), bs_hashes[i], ss_roots[i])
            shard_keys.append(shard_key)

        self.db.put(key, shard_keys.encode())


    def get(self, root: ErasureRoot) -> ShardKeyUnits:
        key = self.prefix + root.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Shards not found in DA")

        data, _ = ShardKeyUnits.decode_from(data)

        return data

    def get_ss_roots(self, root: ErasureRoot) -> SSKeysUnits:
        key = self.prefix + root.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Shards not found in DA")

        data, _ = ShardKeyUnits.decode_from(data)

        ss_roots = SSKeysUnits([])
        for key in data:
            ss_key = SSKeysUnit(key.shard_index, key.segment_shard_root)
            ss_roots.append(ss_key)

        return ss_roots

    def get_ss_root(self, root: ErasureRoot, shard_index: ShardIndex):
        key = self.prefix + root.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Shards not found in DA")

        data, _ = ShardKeyUnits.decode_from(data)

        for key in data:
            ss_key = SSKeysUnit(key.shard_index, key.segment_shard_root)
            if key.shard_index == shard_index:
                return ss_key

        return Null

    def get_bs_hashes(self, root: ErasureRoot) -> BSKeysUnits:
        key = self.prefix + root.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Shards not found in DA")

        data, _ = ShardKeyUnits.decode_from(data)

        bs_hashes = BSKeysUnits([])
        for key in data:
            bs_key = BSKeysUnit(key.shard_index, key.bundle_shard_hash)
            bs_hashes.append(bs_key)

        return bs_hashes

    def get_bs_hash(self, root: ErasureRoot, shard_index: ShardIndex):
        key = self.prefix + root.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Shards not found in DA")

        data, _ = ShardKeyUnits.decode_from(data)

        for key in data:
            bs_key = BSKeysUnit(key.shard_index, key.bundle_shard_hash)
            if key.shard_index == shard_index:
                return bs_key

        return Null

    def delete(self, root: ErasureRoot) -> None:
        key = self.prefix + root.encode()
        self.db.delete(key)