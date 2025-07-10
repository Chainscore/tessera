import logging
from typing import List, Tuple

from tsrkit_types import structure, U8, Bytes
from jam.types.protocol.core import CoreIndex

from jam.audit.audit import AuditingAndJudgement
from jam.consensus.grandpa.finality import Finality

from jam.types.work.report import WorkReport
from jam.logging import get_logger


from jam.network.node import Node
from jam.state.state import State



# Module-specifier logger
logger = get_logger("in_core")


@structure
class AuditProcess:

    node : Node
    audit: AuditingAndJudgement

    def __init__(self, node: Node):
        from jam.settings import settings
        self.audit = AuditingAndJudgement()
        self.settings = settings
        self.node = node
        self.state = State

    def report_assignment(self, node: Node) -> List[Tuple[CoreIndex, WorkReport]]:
        from jam.consensus.grandpa.finality import Finality

        settings = self.settings

        # rho double dagger
        rho = self.state.rho

        # initial rho pending wor reports
        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()

        entropy = latest_block.header.entropy_source

        pending_rho = self.state.load(header_hash=header_hash).rho

        # pre audit reports
        p_a_r = self.audit.report_to_be_audit(available_reports=rho, pending_report=pending_rho)

        # assignment report for auditing to validators
        reports = self.audit.verifiable_random_selection(entropy_source=entropy, bandersnatch_key=self.node.ed_key, pre_audit_report=p_a_r)

        return reports

    def audit_announcement(self, reports: List[Tuple[CoreIndex, WorkReport]]) -> set[Bytes[96]]:

        settings = self.settings

        # initial rho pending wor reports
        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()

        announcement = self.audit.validator_announcement_statement(assign_report=reports, header=header_hash,  ed25519_public=self.node.ed_key, tranche=U8(0))

        return announcement

    def judgment_process(self, reports : List[Tuple[CoreIndex, WorkReport]]):
        from jam.audit.vectors.packages import hash_to_package

        judgment_set = set()

        get_package = None

        for c, r in reports:
            wp_hash = r.package_spec.hash
            for package in hash_to_package:
                for key, value in package.items():
                    if key == wp_hash:
                        get_package = value
                        break
                if get_package:
                    break

            result = self.audit.refine(r=r)
            signature = self.audit.judgment_signature(r=r, refine=result,ed25519_public=self.node.ed_key)
            judgment_set.add(signature)

        return judgment_set
