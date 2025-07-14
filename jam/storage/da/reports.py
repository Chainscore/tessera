from rockstore import RockStore

from jam.types.work.report import WorkReport, WorkReportHash
from jam.storage.da.store import DA


class ReportsDA(DA):
    """
    Reports DA Stores all the reports compiled / received by a node

    Key: Work Report Hash
    Value: Work Report
    """

    def __init__(self, db: RockStore):
        self.prefix = bytes("WREP", "utf-8")
        self.db = db

    def put(self, wr_hash: WorkReportHash, report: WorkReport) -> None:
        key = self.prefix + wr_hash.encode()
        self.db.put(key, report.encode())

    def get(self, wr_hash: WorkReportHash) -> WorkReport:
        key = self.prefix + wr_hash.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Report not found in DA")

        report, _ = WorkReport.decode_from(data)

        return report

    def delete(self, wr_hash: WorkReportHash) -> None:
        key = self.prefix + wr_hash.encode()
        self.db.delete(key)
