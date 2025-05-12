from jam.work_package.package_db import ReportStore
from tests.dummy.dummy_extrinsics import create_dummy_work_report
from tests.dummy.utils import create_dummy_bytes32


def test_report_db():
    db = ReportStore()
    wr_hash = create_dummy_bytes32()
    report = create_dummy_work_report()
    db.put(wr_hash=wr_hash, report=report)
    db_report = db.get(wr_hash=wr_hash)
    assert report == db_report