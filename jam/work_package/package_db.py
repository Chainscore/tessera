from jam.db.kv import KVStore
from jam.merklization import BMRFunctions
from jam.types.work.report import WorkPackageBundle
from jam.types.work.segment import Segments
from jam.types.protocol.core import OpaqueHash, ValidatorIndex
import struct
from typing import Tuple


class SegmentStore:

    def __init__(self):
        self.db_path = "db/segment"
        self.db = KVStore(self.db_path)

    def put(self, export_segment: Segments, paged_proof: Segments):
        print("inserting data")
        merkle = BMRFunctions()
        e = BMRFunctions.cd_merkle_fn(merkle, export_segment)
        seg_bytes = export_segment.encode()
        proof_bytes = paged_proof.encode()
        seg_len = struct.pack("<I", len(seg_bytes))  # 4-byte little-endian

        db_data = seg_len + seg_bytes + proof_bytes
        self.db.put(e.encode(), db_data)

    def get(self, segment_hash) -> Tuple[Segments, Segments]:
        data = self.db.get(bytes(segment_hash))
        if data is None:
            raise KeyError("Segment not found")

        import struct

        # Read the first 4 bytes to extract seg_bytes length
        seg_len = struct.unpack("<I", data[:4])[0]
        seg_bytes = data[4:4 + seg_len]
        proof_bytes = data[4 + seg_len:]

        export_segment, _ = Segments.decode_from(seg_bytes)
        paged_proof, _ = Segments.decode_from(proof_bytes)

        return export_segment, paged_proof

    def delete(self, segment_hash):
        self.db.delete(bytes(segment_hash))

    def close(self):
        self.db.close()


class BundleStore:

    def __init__(self):
        self.db_path = "db/bundle"
        self.db = KVStore(self.db_path)


    def put(self, bundle_root: OpaqueHash, bundle: WorkPackageBundle):
        self.db.put(bundle_root.encode(), bundle.encode())

    def get(self, bundle_root: OpaqueHash) -> WorkPackageBundle:
        bundle = self.db.get(bytes(bundle_root))
        if bundle is None:
            raise KeyError("Key not found")
        decoded_bundle, _ = WorkPackageBundle.decode_from(bundle)
        return decoded_bundle

    def delete(self, bundle_root: OpaqueHash):
        self.db.delete(bytes(bundle_root))

    def close(self):
        self.db.close()


class PackageSegmentMap:
    def __init__(self):
        self.db_path = "db/packageSegmentMap"
        self.db = KVStore(self.db_path)

    def put(self, package_hash: OpaqueHash, segment_root: OpaqueHash):
        self.db.put(package_hash.encode(), segment_root.encode())

    def get(self, package_hash: OpaqueHash) -> OpaqueHash:
        segment_root = self.db.get(bytes(package_hash))
        if segment_root is None:
            raise KeyError("Key not found")
        decoded_root, _ = OpaqueHash.decode_from(segment_root)
        return decoded_root

    def delete(self, package_hash: OpaqueHash):
        self.db.delete(bytes(package_hash))

    def close(self):
        self.db.close()


class SegmentAssurerMap:
    def __init__(self):
        self.db_path = "db/segmentAssurerMap"
        self.db = KVStore(self.db_path)

    def put(self, segment_root: OpaqueHash, erasure_root: OpaqueHash, assurer:ValidatorIndex):
        erasure_bytes=  erasure_root.encode()
        assurer_bytes = assurer.encode()
        erasure_root_len = struct.pack("<H", len(erasure_bytes))
        db_data = erasure_root_len + erasure_bytes + assurer_bytes
        self.db.put(segment_root.encode(), db_data)

    def get(self, segment_root: OpaqueHash) -> Tuple[OpaqueHash, ValidatorIndex]:
        res = self.db.get(bytes(segment_root))
        if res is None:
            raise KeyError("Key not found")
        erasure_root_len = struct.unpack("<I", res[:2])[0]
        erasure_bytes = res[2:2 + erasure_root_len]
        assurer_bytes = res[2 + erasure_root_len:]
        erasure_root, _ = OpaqueHash.decode_from(erasure_bytes)
        assurer, _ = ValidatorIndex.decode_from(assurer_bytes)
        return erasure_root, assurer

    def delete(self, segment_root: OpaqueHash):
        self.db.delete(bytes(segment_root))

    def close(self):
        self.db.close()