from jam.types.work.segment import Segments

from jam.work_package.work_package import WorkPackageProcessing
from tests.dummy.utils import create_dummy_bytes32, create_dummy_bytes, create_dummy_bytes4104
from jam.types.base.sequences.bytes.bytes import Bytes


def test_aval_spec():
    print("starting")
    package_process = WorkPackageProcessing()
    segments: Segments = [create_dummy_bytes4104()]
    # print(bytes(create_dummy_bytes4104()))
    specs = package_process.availability_specifier(package_hash=create_dummy_bytes32(), wp_bundle=Bytes(create_dummy_bytes(12)), export_segments=segments)
    print(specs)