from typing import cast

from tsrkit_types import Vector

from jam.config.logging import logger
from jam.network.quic.server import QuicServerProtocol
from jam.types.work import WorkReport
from tsrkit_types.struct import structure
from jam.types.work.report import WorkReport

from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.types.protocol.crypto import WorkReportHash, Hash
from jam.utils.dummy.dummy_extrinsics import create_dummy_work_report
from jam.types.protocol.crypto import WorkReportHash


@structure
class CE136Data:
    work_report_hash: WorkReportHash


class WorkReportRequest(NetworkProtocol):
    """
    CE 136 Protocol for requesting Work Report

    Protocol Flow:
        Node -> Node

        --> Work-Report Hash
        --> FIN
        <-- Work-Report
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-136-work-report-request
    """

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE136

    def transmit(self, node: Node, data: CE136Data):
        """Request Work Report from Node (server)"""

        message = self._prefix.encode() + data.encode()
        logger.info(f"Requesting Work-Report from {len(node.connections)} Validators")

        # TODO: Use Original Guarantor Connection

        responses = Vector([])
        for client in node.connections:
            data = client.stream_and_close(message=message)
            responses.append(data)

        return responses

    def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """Intercept & Fetch requested Work Report on Node (server)"""
        logger.info("Received Work Report Request")
        data, offset = CE136Data.decode_from(buffer)
        data = cast(CE136Data, data)

        logger.info("Fetching Work Report")
        # TODO: Process received Work Report Query
        report = create_dummy_work_report()
        # Process goes here

        logger.info(f"📩 Processed work report query for WR {data.work_report_hash}")

        # Return requested report to client node
        ack = self._prefix.encode() + report.encode()
        server.stream_and_close(stream_id, ack)

        logger.info("Requested report sent back to Node")

    def client_intercept(self, node: Node, buffer: bytes, stream_id: int) -> WorkReport:
        """Intercept Requested Work Report"""

        logger.info(f"Requested Report received on Node (client) via stream {stream_id}")
        data, offset = WorkReport.decode_from(buffer)
        data = cast(WorkReport, data)

        logger.info("Saving Work Report")
        # TODO: Process & Save Work Report
        # Process goes here

        return data
