import shutil
import tempfile
from jam.merklization import BMRFunctions
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.base.sequences.vector import Vector
from jam.types.work.report import WorkPackageBundle
from jam.work_package.work_package import WorkPackageProcessing
from jam.work_package.package_db import SegmentStore, BundleStore
from jam.db.kv import KVStore
from jam.types.work.manifest import Segments, Segment, ByteArray4104
from tests.dummy.dummy_bundle import create_dummy_bundle
from tests.dummy.utils import create_dummy_bytes32, create_dummy_bytes4104


def test_segment_store():
    print("starting")
    segment_db = SegmentStore()
    segment = create_dummy_bytes4104()
    export_segment = Segments([])
    export_segment.append(segment)
    print(export_segment)
    package_processing = WorkPackageProcessing()
    paged_proof = package_processing.paged_proof(export_segment)
    segment_db.put(export_segment, paged_proof)
    print("stored successfully")
    merkle = BMRFunctions()
    e = BMRFunctions.cd_merkle_fn(merkle, export_segment)
    imports, proof = segment_db.get(e)
    print(imports)
    print("proof: ", proof)
    segment_db.close()

def test_bundle_store():
    bundle_db = BundleStore()
    root = create_dummy_bytes32()
    dummy_bundle = create_dummy_bundle()
    print("dummy bundle:", dummy_bundle)
    bundle_db.put(bundle_root=root, bundle=dummy_bundle)
    fetched_bundle = bundle_db.get(bundle_root=root)
    print(fetched_bundle)
    bundle_db.close()
    print("db closed")

