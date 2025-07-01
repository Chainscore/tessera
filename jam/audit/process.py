from jam.network.node import Node
from jam.audit.audit import AuditingAndJudgement
from jam.state.state import


class Process:
    node: Node

    def __init__(self, node: Node):
        self.node = node
        self.audit = AuditingAndJudgement()


    def announcement(self, ):
        reports = self.audit.report_to_be_audit(pending_report=, )

