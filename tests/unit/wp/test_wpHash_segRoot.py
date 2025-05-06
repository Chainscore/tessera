from jam.work_package.package_db import PackageSegmentMap
from tests.dummy.utils import create_dummy_bytes32


def test_wp_hash_seg_root():
    print("starting")
    db = PackageSegmentMap()
    package_hash = create_dummy_bytes32()
    root = create_dummy_bytes32()
    db.put(package_hash=package_hash, segment_root=root)
    db_root = db.get(package_hash=package_hash)
    assert root == db_root
