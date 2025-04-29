import shutil
import tempfile
from jam.merklization import BMRFunctions
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.base.sequences.vector import Vector
from jam.work_package.work_package import WorkPackageProcessing
from jam.work_package.package_db import SegmentStore
from jam.db.kv import KVStore
from jam.types.work.segment import Segments, Segment, ByteArray4104
from tests.dummy.utils import create_dummy_bytes32


def test_put():
    segment_db = SegmentStore()
    merkle = BMRFunctions()
    # segment = ByteArray32(create_dummy_bytes32())
    # export_segment = Segments([])
    # export_segment.append(segment)
    export_segment: Segments = Segments([])

    for i in range(1):
        val = f"segment {i}".encode()
        val = val.ljust(4104, b'\0')
        new_seg = Segment(ByteArray4104(val))

        export_segment.append(new_seg)

    print(export_segment)
    package_processing = WorkPackageProcessing()
    paged_proof = package_processing.paged_proof(export_segment)
    segment_db.put(export_segment, paged_proof)
    print("stored successfully")
    merkle = BMRFunctions()
    e = BMRFunctions.cd_merkle_fn(merkle, export_segment)
    imports = segment_db.get(e)
    print("fetched imports: ", imports)

