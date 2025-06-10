from rockstore import RockStore

from jam.utils.dummy.dummy_extrinsics import create_dummy_work_report
from jam.work_package.stores.mappings import PackageSegmentMap


def test_wp_hash_seg_root(db_path):
    d3l = RockStore(db_path)
    db = PackageSegmentMap(d3l)
    report = create_dummy_work_report()
    package_hash = report.package_spec.hash

    db.put(report)
    db_root = db.get(package_hash)
    assert report.package_spec.exports_root == db_root
