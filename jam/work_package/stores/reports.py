from jam.db.kv import KVStore
from jam.types.protocol.crypto import Hash
from jam.work_package.store import DA
from jam.types.work.report import WorkReport, WorkReportHash

class ReportsDA(DA):
    """
    Reports DA Stores all the segments shards built / fetched by a node

    Key: Segments Shard Root
    Value: Segments Shard (Vector[Segment Shard])
    """

    def __init__(self, db: KVStore):
        self.prefix = bytes("WR", 'utf-8')
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