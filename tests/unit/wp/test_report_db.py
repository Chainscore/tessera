from rockstore import RockStore

from jam.utils.dummy.dummy_extrinsics import create_dummy_work_report
from jam.utils.dummy.utils import create_dummy_bytes32
from jam.work_package.stores.reports import ReportsDA


def test_report_db(db_path):
    db = RockStore(db_path)
    d3l = ReportsDA(db)

    wr_hash = create_dummy_bytes32()
    report = create_dummy_work_report()
    d3l.put(wr_hash=wr_hash, report=report)
    db_report = d3l.get(wr_hash=wr_hash)
    assert report == db_report