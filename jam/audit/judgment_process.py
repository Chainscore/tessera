from tsrkit_types import Dictionary

from jam.network import node
from jam.work_package.bundler import Bundler
from jam.work_package.processor import Processor
from typing import Tuple
from jam.types.protocol.crypto import WorkReportHash
from jam.types.work.report import WorkReport
from jam.types.work.package import WorkPackageBundle, WorkPackage, WorkItems
from jam.audit.test_work_package import work_package_bundle_test


# TODO: 1. We have an assurance list => [(0, Wo), (1, W1), ... , (341, W341)]  (generate assurance => Protocol: 141)
# TODO: 2. Get report to be Audit => [0, W0]
# TODO: 3. Using work_report erasure root => get all bundle shard  (protocol 137, 138)
# TODO: 4. Re-construct the work-package and generate work package hash (hash ==  work_report.spec.hash)
# TODO: 5. Refine logic
# TODO: 6. match report hash
# TODO: 7. Generate judgment  (Protocol: 145)

class AuditBundler:
    def __init__(self):
        self.bundle = Bundler()
        self.process = Processor()

    def audit_report(self, work_report: WorkReport) ->  Tuple[WorkReport, WorkReportHash]:
        report, report_hash = self.process.process_bundle(core=1, bundle=work_package_bundle_test, sr_lookup=Dictionary({}))
        return report, report_hash


