import logging

from tsrkit_types import structure
from jam.audit.audit import AuditingAndJudgement
from jam.consensus.grandpa.finality import Finality

from jam.logging import get_logger

# Module-specifier logger

from jam.network.node import Node
from jam.state.state import State

logger = get_logger("in_core")


@structure
class AuditProcess:

    node : Node

    def __init__(self, node: Node):
        from jam.settings import settings
        self.audit = AuditingAndJudgement()
        self.settings = settings
        self.node = node
        self.state = State

    def audit_announcement(self, ):
        settings = self.settings

        # recent block header hash
        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()

        # get rho Available reports
        rho = self.state.rho

        pending_rho = self.state.load(header_hash=header_hash)
        rho_dagger = pending_rho.rho


        try:
            logger.info(f"Start processing Available Work Report to be Audit")

            reports = self.audit.report_to_be_audit(available_reports=rho, pending_report=rho_dagger)

            assignment = self.audit.verifiable_random_selection(entropy_source=header_hash, bandersnatch_key=self.node.ed_pvt_key, pre_report=reports)


        except Exception as e:
            logging.error("Failed to announce work_report")