from dataclasses import dataclass
from typing import cast

from jam.config.logging import logger
from jam.network.quic import QuicServerProtocol
from jam.types.base.integers import Int
from jam.types.work.report import WorkPackageBundle

from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.utils.json import JsonSerde

from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature
from jam.types.protocol.core import CoreIndex
from jam.work_package.work_package import SegmentRootLookup

@decodable_dataclass
@dataclass
class CoreSegment(Codable, JsonSerde):
    core_index : CoreIndex
    length : Int
    segment_root_map : SegmentRootLookup


@decodable_dataclass
@dataclass
class Credential(Codable, JsonSerde):
    work_report_hash : WorkReportHash
    ed25519_signature : Ed25519Signature


@decodable_dataclass
@dataclass
class CE134Data(Codable, JsonSerde):
    core_segment: CoreSegment
    work_package_bundle : WorkPackageBundle

class WorkPackageSharing(NetworkProtocol):
    """
    CE 134 Protocol for sharing Work Package Bundle among Guarantors

    Protocol Flow:
        Guarantor -> Guarantor

        --> Core Index ++ Segments-Root Mappings
        --> Work-Package Bundle
        --> FIN
        <-- Work-Report Hash ++ Ed25519 Signature
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-134-work-package-sharing
    """

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE134

    def transmit(self, node: Node, data: CE134Data):
        """Request Work Report from Node (server)"""

        logger.info(f"Transmitting Work-Package-Bundle to {len(node.connections)} Guarantors")
        # TODO: Use Actual Guarantors Connections

        stream_a = self._prefix.encode() + data.core_segment.encode()
        stream_b = data.work_package_bundle.encode()

        for client in node.connections:
            stream_id = client.stream_and_keep_open(message=stream_a)
            client.stream_and_close(message=stream_b, stream_id=stream_id)

    def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """Intercept Work Package Bundle & Build Work Report on Core's Guarantors (server)"""

        logger.info("Received Work Package Bundle from OG Guarantor")
        data, offset = CE134Data.decode_from(buffer)
        data = cast(CE134Data, data)

        logger.info("Building Work Report")
        # TODO: Process received Work Package Bundle, Build Report & Return Credential if validated
        from jam.utils.dummy.dummy_package import create_dummy_credential
        credential = create_dummy_credential()
        # Process goes here

        # Return Credential to OG Guarantor
        ack = self._prefix.encode() + credential.encode()
        server.stream_and_close(stream_id, ack)

        logger.info("Report's Credential sent back to OG Guarantor")

    def client_intercept(self, buffer: bytes, stream_id: int):
        """Intercept validated Work Report from guarantors"""

        logger.info(f"Report's Credential received on OG guarantor (client) via stream {stream_id}")
        data, offset = Credential.decode_from(buffer)
        data = cast(Credential, data)

        logger.info("Distributing this Work Report after achieving majority")
        # TODO: Save Work Report & Check Majority & Distribute
        # Process goes here