from typing import cast, TYPE_CHECKING

from jam.config.logging import get_logger

if TYPE_CHECKING:
    from jam.network.quic.server import QuicServerProtocol
    from jam.network.node import Node

from tsrkit_types.struct import structure
from jam.network.protocols.base import NetworkProtocol, PrefixType

from jam.types.work import WorkReport
from jam.types.protocol.core import TimeSlot

# Module-specific logger
logger = get_logger("network")


@structure
class CE135Data:
    report: WorkReport
    slot: TimeSlot


class WorkReportDistribution(NetworkProtocol):
    """
    CE 135 Protocol for distributing Guaranteed Work Report

    Protocol Flow:
        Guarantor -> Validator

        --> Guaranteed Work-Report
        --> FIN
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-135-work-report-distribution
    """

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE135

    def transmit(self, node: "Node", data: CE135Data):
        """Transmit Work Report from Guarantor (client) to Validator (server)"""

        # TODO: Add Validator Index & Signature as per GP
        message = self._prefix.encode() + data.report.encode() + data.slot.encode()
        
        logger.info(
            "Distributing guaranteed work report to validators",
            node_name=node.name,
            time_slot=int(data.slot),
            validator_count=len(node.connections),
            message_size=len(message),
            core_index=int(data.report.core_index)
        )
        
        distributed_count = 0
        # TODO: Use All Validators Connections
        for client in node.connections:
            try:
                client.stream_and_close(message=message)
                distributed_count += 1
                
                logger.debug(
                    "Work report distributed to validator",
                    node_name=node.name,
                    time_slot=int(data.slot),
                    core_index=int(data.report.core_index)
                )
            except Exception as e:
                logger.error(
                    "Failed to distribute work report to validator",
                    node_name=node.name,
                    error=str(e),
                    error_type=type(e).__name__
                )
        
        logger.info(
            "Work report distribution completed",
            node_name=node.name,
            distributed_to=distributed_count,
            total_validators=len(node.connections),
            time_slot=int(data.slot),
            core_index=int(data.report.core_index)
        )

    def server_intercept(self, buffer: bytes, server: "QuicServerProtocol", stream_id: int):
        """Intercept & Process Work Report on Validator (server)"""

        try:
            logger.debug(
                "Received work report distribution",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )
            
            data, offset = CE135Data.decode_from(buffer)
            data = cast(CE135Data, data)

            logger.info(
                "Processing guaranteed work report",
                stream_id=stream_id,
                time_slot=int(data.slot),
                core_index=int(data.report.core_index),
                authorizer_hash=data.report.authorizer_hash.hex()[:16] + "..."
            )
            
            # TODO: Process received Work Report
            # Process goes here

            logger.info(
                "Work report processed successfully",
                stream_id=stream_id,
                time_slot=int(data.slot),
                core_index=int(data.report.core_index)
            )

            # Send Acknowledgement
            ack = self._prefix.encode() + b""
            server.stream_and_close(stream_id, ack)

            logger.debug(
                "Acknowledgement sent to guarantor",
                stream_id=stream_id,
                ack_size=len(ack)
            )
            
        except Exception as e:
            logger.error(
                "Error processing work report distribution",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )

    def client_intercept(self, buffer: bytes, stream_id: int):
        """Intercept Acknowledgement"""

        logger.info(
            "Work report acknowledgement received from validator",
            stream_id=stream_id,
            buffer_size=len(buffer)
        )


