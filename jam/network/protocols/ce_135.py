from dataclasses import dataclass
from typing import cast

from jam.config.logging import logger
from jam.network.quic.server import QuicServerProtocol

from jam.utils.json import JsonSerde
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.network.protocols.base import NetworkProtocol, PrefixType

from jam.types.work.report import WorkReport
from jam.types.protocol.core import TimeSlot


@decodable_dataclass
@dataclass
class CE135Data(Codable, JsonSerde):
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

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE135

    def transmit(self, node: Node, data: CE135Data):
        """Transmit Work Report from Guarantor (client) to Validator (server)"""

        # TODO: Add Validator Index & Signature as per GP
        message = self._prefix.encode() + data.report.encode() + data.slot.encode()
        logger.info(f"Transmitting Guaranteed Work-Report to {len(node.connections)} Validators")
        # TODO: Use All Validators Connections

        for client in node.connections:
            client.stream_and_close(message=message)

    def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """Intercept & Process Work Report on Validator (server)"""

        logger.info("Received Work Report")
        data, offset = CE135Data.decode_from(buffer)
        data = cast(CE135Data, data)

        logger.info("Processing Work Report")
        # TODO: Process received Work Report
        # Process goes here

        logger.info(f"📩 Processed work report : {data.report} with slot {data.slot}")

        # Send Acknowledgement
        ack = self._prefix.encode() + b""
        server.stream_and_close(stream_id, ack)

        logger.info("Sent acknowledgement back to guarantor")

    def client_intercept(self, buffer: bytes, stream_id: int):
        """Intercept Acknowledgement"""

        logger.info(f"Guaranteed Report received on Guarantor Node via stream {stream_id}")


