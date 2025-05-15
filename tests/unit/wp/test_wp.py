from jam.merklization import BMRFunctions
from jam.work_package.stores.segments import SegmentsDA
from jam.work_package.processor import WorkPackageProcessing
from jam.db.kv import KVStore
from jam.types.work.manifest import Segments, Segment, ByteArray4104, ProvedSegments
from tests.dummy.dummy_bundle import create_dummy_bundle
from tests.dummy.utils import create_dummy_bytes32, create_dummy_bytes4104


def test_segment_store(db_path):
    print("starting")
    d3l = KVStore(db_path)
    segment_db = SegmentsDA(d3l)

    segment = create_dummy_bytes4104()
    export_segment = Segments([])
    export_segment.append(segment)
    print(export_segment)
    package_processing = WorkPackageProcessing()
    paged_proof = package_processing.paged_proof(export_segment)

    proved_segments = ProvedSegments(segment=export_segment, proof=paged_proof)

    merkle = BMRFunctions()
    e = merkle.cd_merkle_fn(export_segment)
    segment_db.put(e, proved_segments)
    print("stored successfully")

    data = segment_db.get(e)

    assert  (export_segment, paged_proof) == data
    segment_db.close()

