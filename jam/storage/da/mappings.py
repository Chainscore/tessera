from typing import Tuple

from rockstore import RockStore

from jam.models.protocol.crypto import Hash
from jam.models.protocol.core import (
    WorkPackageHash,
    ExportsRoot,
    ErasureRoot,
    WorkReportHash,
)
from jam.models.work.report import WorkReport
from jam.models.work.manifest import Assurers, ReportAssurers

from jam.storage.da.store import DA


class PackageSegmentMap(DA):
    """
    PackageSegmentMap Maps all the packages to their segments root.

    Key: Work Package Hash
    Value: Segments Root
    """

    def __init__(self, db: RockStore):
        self.prefix = bytes("WPSR", "utf-8")
        self.db = db

    def put(self, report: WorkReport) -> None:
        key = self.prefix + report.package_spec.hash.encode()
        data = report.package_spec.exports_root

        self.db.put(key, data.encode())

    def get(self, wp_hash: WorkPackageHash) -> ExportsRoot:
        key = self.prefix + wp_hash.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Segment Root not found in DA")

        report, _ = ExportsRoot.decode_from(data)

        return report

    def delete(self, wp_hash: WorkPackageHash) -> None:
        key = self.prefix + wp_hash.encode()
        self.db.delete(key)


class SegmentErasureMap(DA):
    """
    SegmentErasureMap Maps all the segments root to their erasure root.

    Key: Segments Root
    Value: Erasure Root
    """

    def __init__(self, db: RockStore):
        self.prefix = bytes("SR-ER", "utf-8")
        self.db = db

    def put(self, root: ExportsRoot, data: ErasureRoot) -> None:
        key = self.prefix + root.encode()
        self.db.put(key, data.encode())

    def get(self, root: ExportsRoot) -> ErasureRoot:
        key = self.prefix + root.encode()
        data = self.db.get(key)

        if data is None:
            raise KeyError("Erasure Root not found in DA")

        root, _ = ErasureRoot.decode_from(data)
        return root

    def delete(self, root: ExportsRoot) -> None:
        key = self.prefix + root.encode()
        self.db.delete(key)


class ErasureAssurerMap(DA):
    """
    ErasureAssurerMap Maps all the erasure root to their work report and assurers.

    Key: Erasure Root
    Value: Work Report Hash, Assurers
    """

    def __init__(self, db: RockStore):
        self.prefix = bytes("ER-WR-A", "utf-8")
        self.db = db

    def put(self, report: WorkReport, assurers: Assurers) -> None:
        report_hash = Hash.blake2b(report.encode())

        key = self.prefix + report.package_spec.erasure_root.encode()
        data = ReportAssurers(report_hash, assurers)

        self.db.put(key, data.encode())

    def get(self, root: ErasureRoot) -> Tuple[WorkReportHash, Assurers]:
        key = self.prefix + root.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Assurer & Report not found in DA")

        data, _ = ReportAssurers.decode_from(data)

        return data.report_hash, data.assurers

    def delete(self, root: ErasureRoot) -> None:
        key = self.prefix + root.encode()
        self.db.delete(key)


class ReportHashAssurerMap(DA):
    """
    ReportHashAssurerMap Maps all the report hash to their assurers.

    Key: Report Hash
    Value: Assurers
    """

    def __init__(self, db: RockStore):
        self.prefix = bytes("WRH-A", "utf-8")
        self.db = db

    def put(self, report: WorkReport, assurers: Assurers) -> None:
        report_hash = Hash.blake2b(report.encode())

        key = self.prefix + report_hash.encode()
        data = assurers

        self.db.put(key, data.encode())

    def get(self, report_hash: WorkReportHash) -> Assurers:
        key = self.prefix + report_hash.encode()
        data = self.db.get(key)
        if data is None:
            raise KeyError("Assurers not found in DA")

        data, _ = Assurers.decode_from(data)

        return data

    def delete(self, report_hash: WorkReportHash) -> None:
        key = self.prefix + report_hash.encode()
        self.db.delete(key)
