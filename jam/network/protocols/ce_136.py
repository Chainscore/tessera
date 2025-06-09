from typing import cast, TYPE_CHECKING

from jam.config.logging import get_logger

if TYPE_CHECKING:
    from jam.network.quic.server import QuicServerProtocol
    from jam.network.node import Node

from jam.types.work import WorkReport
from tsrkit_types.struct import structure
from jam.network.protocols.base import NetworkProtocol, PrefixType

from jam.types.protocol.crypto import WorkReportHash, Hash
from jam.utils.dummy.dummy_extrinsics import create_dummy_work_report

# Module-specific logger
logger = get_logger("network")


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

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE136

    def transmit(self, node: "Node", data: CE136Data):
        """Request Work Report from Node (server)"""

        message = self._prefix.encode() + data.work_report_hash.encode()
        
        logger.info(
            "Requesting work report from nodes",
            node_name=node.name,
            work_report_hash=data.work_report_hash.hex()[:16] + "...",
            node_count=len(node.connections),
            message_size=len(message)
        )

        requested_count = 0
        # TODO: Use Original Guarantor Connection
        for client in node.connections:
            try:
                client.stream_and_close(message=message)
                requested_count += 1
                
                logger.debug(
                    "Work report request sent to node",
                    node_name=node.name,
                    work_report_hash=data.work_report_hash.hex()[:16] + "..."
                )
            except Exception as e:
                logger.error(
                    "Failed to send work report request to node",
                    node_name=node.name,
                    error=str(e),
                    error_type=type(e).__name__
                )
        
        logger.info(
            "Work report request completed",
            node_name=node.name,
            requested_from=requested_count,
            total_nodes=len(node.connections),
            work_report_hash=data.work_report_hash.hex()[:16] + "..."
        )

    def server_intercept(self, buffer: bytes, server: "QuicServerProtocol", stream_id: int):
        """Intercept & Fetch requested Work Report on Node (server)"""

        try:
            logger.debug(
                "Received work report request",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )
            
            data, offset = CE136Data.decode_from(buffer)
            data = cast(CE136Data, data)

            logger.info(
                "Fetching requested work report",
                stream_id=stream_id,
                work_report_hash=data.work_report_hash.hex()[:16] + "..."
            )
            
            # TODO: Process received Work Report Query
            report = create_dummy_work_report()
            # Process goes here

            logger.info(
                "Work report fetched successfully",
                stream_id=stream_id,
                work_report_hash=data.work_report_hash.hex()[:16] + "...",
                report_size=len(report.encode())
            )

            # Return requested report to client node
            ack = self._prefix.encode() + report.encode()
            server.stream_and_close(stream_id, ack)

            logger.debug(
                "Work report sent to requesting node",
                stream_id=stream_id,
                response_size=len(ack)
            )
            
        except Exception as e:
            logger.error(
                "Error processing work report request",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )

    def client_intercept(self, buffer: bytes, stream_id: int):
        """Intercept Requested Work Report"""

        try:
            logger.debug(
                "Received requested work report",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )
            
            data, offset = WorkReport.decode_from(buffer)
            data = cast(WorkReport, data)

            h = Hash.blake2b(data.encode())

            logger.info(
                "Processing received work report",
                stream_id=stream_id,
                work_report_hash=h.hex()[:16] + "...",
                core_index=int(data.core_index)
            )
            
            # TODO: Process & Save Work Report
            # Process goes here
            
            logger.info(
                "Work report saved successfully",
                stream_id=stream_id,
                work_report_hash=h.hex()[:16] + "..."
            )
        except Exception as e:
            logger.error(
                "Error processing received work report",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )
