from jam.db.kv import KVStore
from jam.merklization import BMRFunctions
from jam.types.base.sequences.bytes.byte_array import ByteArray12
from jam.types.base.sequences.vector import Vector
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.work.report import WorkPackageBundle, ShardKeysVector, ShardKeys, SegmentsShard, WorkReports, WorkReport
from jam.types.work.segment import Segments, SegmentsWithProof, ErasureRootAssurers, Assurers
from jam.types.protocol.core import OpaqueHash, ValidatorIndex
from typing import Tuple, Union, Optional
from jam.types.base.integers.fixed import U16
from jam.types.work.report import BundleShard

class SegmentStore:

    def __init__(self):
        self.db_path = "/home/faizahmad817/tessera/db/segment"
        self.db = KVStore(self.db_path)

    def put(self, export_segment: Segments, paged_proof: Segments):
        merkle = BMRFunctions()
        e = BMRFunctions.cd_merkle_fn(merkle, export_segment)
        data = SegmentsWithProof(segment=export_segment, proof=paged_proof)
        self.db.put(e.encode(), data.encode())

    def get(self, segment_hash: OpaqueHash) -> Tuple[Segments, Segments]:
        data = self.db.get(segment_hash.encode())
        if data is None:
            raise KeyError("Segment not found")

        decoded_data, _ = SegmentsWithProof.decode_from(data)
        export_segment = decoded_data.segments
        paged_proof = decoded_data.proof

        return export_segment, paged_proof

    def delete(self, segment_hash:OpaqueHash):
        self.db.delete(segment_hash.encode())

    def close(self):
        self.db.close()


class BundleStore:

    def __init__(self):
        self.db_path = "/home/faizahmad817/tessera/db/bundle"
        self.db = KVStore(self.db_path)

    def put(self, bundle_root: OpaqueHash, bundle: WorkPackageBundle):
        self.db.put(bundle_root.encode(), bundle.encode())

    def get(self, bundle_root: OpaqueHash) -> WorkPackageBundle:
        bundle = self.db.get(bundle_root.encode())
        if bundle is None:
            raise KeyError("Key not found")
        decoded_bundle, _ = WorkPackageBundle.decode_from(bundle)
        return decoded_bundle

    def delete(self, bundle_root: OpaqueHash):
        self.db.delete(bundle_root.encode())

    def close(self):
        self.db.close()


class PackageSegmentMap:
    def __init__(self):
        self.db_path = "/home/faizahmad817/tessera/db/packageSegmentMap"
        self.db = KVStore(self.db_path)

    def put(self, package_hash: OpaqueHash, segment_root: OpaqueHash):
        self.db.put(package_hash.encode(), segment_root.encode())

    def get(self, package_hash: OpaqueHash) -> OpaqueHash:
        segment_root = self.db.get(package_hash.encode())
        if segment_root is None:
            raise KeyError("Key not found")
        decoded_root, _ = OpaqueHash.decode_from(segment_root)
        return decoded_root

    def delete(self, package_hash: OpaqueHash):
        self.db.delete(package_hash.encode())

    def close(self):
        self.db.close()


class SegmentAssurerMap:
    def __init__(self):
        self.db_path = "/home/faizahmad817/tessera/db/segmentAssurerMap"
        self.db = KVStore(self.db_path)

    def put(self, segment_root: OpaqueHash, erasure_root: OpaqueHash, assurers:Assurers):
        data = ErasureRootAssurers(erasure_root=erasure_root, assurers=assurers)
        self.db.put(segment_root.encode(), data.encode())

    def get(self, segment_root: OpaqueHash) -> Tuple[OpaqueHash, ValidatorIndex]:
        res = self.db.get(segment_root.encode())
        if res is None:
            raise KeyError("Key not found")

        decoded_data , _ = ErasureRootAssurers.decode_from(res)
        return decoded_data.erasure_root, decoded_data.assurers

    def delete(self, segment_root: OpaqueHash):
        self.db.delete(segment_root.encode())

    def close(self):
        self.db.close()


class ErasureSegmentMap:
    def __init__(self):
        self.db_path = "/home/faizahmad817/tessera/db/erasureSegmentMap"
        self.db = KVStore(self.db_path)

    def put(self, erasure_root: OpaqueHash, segment_root: OpaqueHash):
        self.db.put(erasure_root.encode(), segment_root.encode())

    def get(self, erasure_root: OpaqueHash) -> OpaqueHash:
        res = self.db.get(erasure_root.encode())
        if res is None:
            raise KeyError("Key not found")
        segment_root, _ = OpaqueHash.decode_from(res)
        return segment_root

    def delete(self, erasure_root: OpaqueHash):
        self.db.delete(erasure_root.encode())

    def close(self):
        self.db.close()


class ErasureShardsKeysMap:
    def __init__(self):
        self.db_path = "/home/faizahmad817/tessera/db/erasureShardsMap"
        self.db = KVStore(self.db_path)

    @staticmethod
    def make_value(segments_shard_roots: Vector[OpaqueHash], bundles_hashes: Vector[OpaqueHash]):
        value = ShardKeysVector()
        for i in range(len(segments_shard_roots)):
            value.append(ShardKeys(segment_shard_root=segments_shard_roots[i], bundle_shard_hash=bundles_hashes[i]))
        return value

    def put(self, erasure_root: OpaqueHash, segments_shard_roots: Vector[OpaqueHash], bundles_hashes: Vector[OpaqueHash]):
        value = self.make_value(segments_shard_roots, bundles_hashes).encode()
        self.db.put(erasure_root.encode(), value)

    def get_shards_keys(self, erasure_root: OpaqueHash, shard_index: Optional[U16] = None) -> Union[ShardKeysVector, ShardKeys]:
        res = self.db.get(erasure_root.encode())
        if res is None:
            raise KeyError("Key not found")

        decoded_shard_keys_vector, _ = ShardKeysVector.decode_from(res)
        if shard_index is None:
            return decoded_shard_keys_vector
        decoded_shard_keys: ShardKeys = decoded_shard_keys_vector[shard_index]
        return decoded_shard_keys

    def get_segments_shard(self, erasure_root: OpaqueHash, shard_index: U16) -> SegmentsShard:
        keys: ShardKeys = self.get_shards_keys(erasure_root, shard_index)
        segment_shard_db = SegmentShardMap()
        return segment_shard_db.get(keys.segment_shard_root)

    def get_segment_shard(self, erasure_root: OpaqueHash, shard_index: U16, segment_index) -> ByteArray12:
        segments_shard: SegmentsShard = self.get_segments_shard(erasure_root, shard_index)
        return segments_shard[segment_index]

    def get_bundle_shard(self, erasure_root: OpaqueHash, shard_index: U16):
        keys: ShardKeys = self.get_shards_keys(erasure_root, shard_index)
        bundle_shard_db = BundleShardMap()
        return bundle_shard_db.get(keys.bundle_shard_hash)

    def delete(self, erasure_root: OpaqueHash):
        self.db.delete(erasure_root.encode())

    def close(self):
        self.db.close()


class SegmentShardMap:
    def __init__(self):
        self.db_path = "/home/faizahmad817/tessera/db/segmentShardMap"
        self.db = KVStore(self.db_path)

    def put(self, segments_shard_root: OpaqueHash,
            segments_shard: SegmentsShard):
        self.db.put(segments_shard_root.encode(), segments_shard.encode())

    def get(self, segments_shard_root: OpaqueHash) -> SegmentsShard:
        res = self.db.get(segments_shard_root.encode())
        if res is None:
            raise KeyError("Key not found")
        decoded_data, _ = SegmentsShard.decode_from(res)
        return decoded_data

    def delete(self, segments_shard_root: OpaqueHash):
        self.db.delete(segments_shard_root.encode())

    def close(self):
        self.db.close()


class BundleShardMap:
    def __init__(self):
        self.db_path = "/home/faizahmad817/tessera/db/BundleShardMap"
        self.db = KVStore(self.db_path)

    def put(self, bundle_hash: OpaqueHash,
            bundle_shard: Bytes):
        self.db.put(bundle_hash.encode(), bundle_shard.encode())

    def get(self, segments_shard_root: OpaqueHash) -> SegmentsShard:
        res = self.db.get(segments_shard_root.encode())
        if res is None:
            raise KeyError("Key not found")
        decoded_data, _ = Bytes.decode_from(res)
        return decoded_data

    def delete(self, segments_shard_root: OpaqueHash):
        self.db.delete(segments_shard_root.encode())

    def close(self):
        self.db.close()


class ReportStore:

    def __init__(self):
        self.db_path = "/home/faizahmad817/tessera/db/report"
        self.db = KVStore(self.db_path)

    def put(self, wr_hash: OpaqueHash, report: WorkReport):
        self.db.put(wr_hash.encode(), report.encode())

    def get(self, wr_hash: OpaqueHash) -> WorkReport:
        report = self.db.get(wr_hash.encode())
        if report is None:
            raise KeyError("Report not found")
        decoded_report, _ = WorkReport.decode_from(report)

        return decoded_report

    def delete(self, wr_hash: OpaqueHash):
        self.db.delete(wr_hash.encode())

    def close(self):
        self.db.close()
