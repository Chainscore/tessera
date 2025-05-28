from typing import Any

from jam.network.protocols.base import NetworkProtocol, PrefixType


class AuditAnnouncement(NetworkProtocol):
    """
    CE 144 Protocol (Audit announcement ) => Announcement of requirement to audit.

    Protocol Flow:
        Auditor -> Auditor

        --> Header_Hash ++ Tranche ++ Announcement
        --> Evidence
        --> FIN
        <-- FIN

    sources:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-144-audit-announcement
    """
    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE144

    # async def transmit(self, node: Node, data: Any):
