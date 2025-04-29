from dataclasses import dataclass
from typing import cast

from jam.config.logging import logger

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

        for client in node.connections:
            client.stream_and_close(message=message)

    @classmethod
    def server_intercept(cls, buffer: bytes) -> CE135Data:
        """Intercept & Process Work Report on Validator (server)"""

        logger.info("Received Work Report")
        data, offset = CE135Data.decode_from(buffer)
        data = cast(CE135Data, data)

        logger.info("Processing Work Report")
        # TODO: Process received Work Report
        # process goes here

        return data

    @classmethod
    def client_intercept(cls, buffer: bytes):
        """Acknowledgement"""
        logger.info("Guaranteed Report received on Guarantor Node")


