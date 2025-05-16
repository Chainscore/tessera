from jam.storage.db.kv import KVStore
from jam.work_package.stores.mappings import PackageSegmentMap
from tests.dummy.dummy_extrinsics import create_dummy_work_report
from tests.dummy.utils import create_dummy_bytes32


def test_wp_hash_seg_root(db_path):
    print("starting")
    d3l = KVStore(db_path)
    db = PackageSegmentMap(d3l)
    report = create_dummy_work_report()
    package_hash = report.package_spec.hash

    db.put(report)
    db_root = db.get(package_hash)
    assert report.package_spec.exports_root == db_root
