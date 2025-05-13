from jam.types.base.sequences.vector import Vector
from jam.types.work.report import WorkPackageBundle
from jam.types.work.manifest import Segments, MultiSegments
from tests.dummy.dummy_package import create_dummy_package
from tests.dummy.utils import create_dummy_bytes, create_dummy_bytes4104, create_dummy_bytes32
from jam.types.base.sequences.bytes.bytes import Bytes

def create_dummy_bundle():
    segment = create_dummy_bytes4104()
    export_segment = Segments([segment])
    multi_seg = MultiSegments([export_segment])

    return WorkPackageBundle(
        package=create_dummy_package(),
        extrinsics=Vector(Vector(Bytes(create_dummy_bytes(12)))),
        import_segments= multi_seg,
        justifications=Vector(Vector(Vector(create_dummy_bytes32())))
    )