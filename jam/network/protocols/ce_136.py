from dataclasses import dataclass
from typing import cast, Tuple

from jam.config.logging import logger
from jam.types import WorkReport

from jam.utils.json import JsonSerde
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.network.protocols.base import NetworkProtocol, PrefixType

from jam.types.protocol.crypto import WorkReportHash, Hash
from tests.dummy.dummy_extrinsics import create_dummy_work_report


@decodable_dataclass
@dataclass
class CE136Data(Codable, JsonSerde):
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

        message = self._prefix.encode() + data.work_report_hash.encode()
        logger.info(f"Requesting Work-Report from {len(node.connections)} Validators")

        for client in node.connections:
            client.stream_and_close(message=message)

    @classmethod
    def server_intercept(cls, buffer: bytes) -> Tuple[CE136Data, WorkReport]:
        """Intercept & Fetch requested Work Report on Node (server)"""

        logger.info("Received Work Report Request")
        data, offset = CE136Data.decode_from(buffer)
        data = cast(CE136Data, data)

        logger.info("Fetching Work Report")
        # TODO: Process received Work Report Query
        # process goes here

        fetched_report = create_dummy_work_report()

        return data, fetched_report

    @classmethod
    def client_intercept(cls, buffer: bytes) -> Tuple[WorkReport, WorkReportHash]:
        """Acknowledgement"""

        logger.info("Requested Report received on Node (client)")
        data, offset = WorkReport.decode_from(buffer)
        data = cast(WorkReport, data)

        h = Hash.blake2b(data.encode())

        logger.info("Saving Work Report")
        # TODO: Process & Save Work Report
        # process goes here

        return data, h
