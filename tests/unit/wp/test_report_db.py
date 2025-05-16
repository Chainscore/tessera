from jam.storage.db.kv import KVStore
from jam.work_package.stores.reports import ReportsDA
from tests.dummy.dummy_extrinsics import create_dummy_work_report
from tests.dummy.utils import create_dummy_bytes32


def test_report_db(db_path):
    db = KVStore(db_path)
    d3l = ReportsDA(db)

    wr_hash = create_dummy_bytes32()
    report = create_dummy_work_report()
    d3l.put(wr_hash=wr_hash, report=report)
    db_report = d3l.get(wr_hash=wr_hash)
    assert report == db_report