from dataclasses import dataclass
from typing import cast

from jam.config.logging import logger
from jam.network.quic import QuicServerProtocol
from jam.types import Vector
from jam.types.base.integers import Int
from jam.types.work.report import WorkPackageBundle

from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.utils.json import JsonSerde

from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, Hash
from jam.types.protocol.core import CoreIndex
from jam.work_package.processor import SegmentRootLookup, WorkPackageProcessing
from tests.dummy.utils import create_dummy_bytes64
import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jam.ring_vrf.ietf.ietf import IETF_VRF


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

    async def transmit(self, node: Node, data: CE134Data):
        """Request Work Report from Node (server)"""

        logger.info(f"Transmitting Work-Package-Bundle to {len(node.connections)} Guarantors")
        # TODO: Use Actual Guarantors Connections

        stream_a = self._prefix.encode() + data.core_segment.encode()
        stream_b = data.work_package_bundle.encode()

        responses = Vector([])
        for client in node.connections:
            stream_id = client.stream_and_keep_open(message=stream_a)
            data = await client.stream_and_close(message=stream_b, stream_id=stream_id)
            responses.append(data)

        return responses

    def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """Intercept Work Package Bundle & Build Work Report on Core's Guarantors (server)"""

        logger.info("Received Work Package Bundle from OG Guarantor")
        data, offset = CE134Data.decode_from(buffer)
        data = cast(CE134Data, data)

        logger.info("Building Work Report")
        # TODO: Process received Work Package Bundle, Build Report & Return Credential if validated

        # Process goes here
        # Generating report from work package bundle
        wp_processing = WorkPackageProcessing()
        report, report_hash = wp_processing.bundle_process(core=data.core_segment.core_index, bundle=data.work_package_bundle,
                                     segment_lookup=data.core_segment.segment_root_map)

        # TODO: Establish some connection with node so as to access keys.
        port = 30333
        my_keys = json.load(open("seeds/keys.json"))[str(port)]
        ed25519_key = Ed25519PrivateKey.from_private_bytes(
            bytes.fromhex(my_keys["ed25519_private"][2:])
        )

        # Build Guarantee
        payload =  report.core_index.encode() + report.encode()
        guarantee = b"jam_guarantee" + Hash.blake2b(payload).encode()

        # Sign the Guarantee
        sign = Ed25519Signature(ed25519_key.sign(guarantee))

        # Build Credential
        cred = Credential(work_report_hash=report_hash, ed25519_signature=sign)

        # Return Credential to OG Guarantor
        ack = self._prefix.encode() + cred.encode()
        server.stream_and_close(stream_id, ack)

        logger.info("Report's Credential sent back to OG Guarantor")

    def client_intercept(self, buffer: bytes, stream_id: int) -> Credential:
        """Intercept validated Work Report from guarantors"""

        logger.info(f"Report's Credential received on OG guarantor (client) via stream {stream_id}")
        data, offset = Credential.decode_from(buffer)
        data = cast(Credential, data)

        logger.info("Distributing this Work Report after achieving majority")
        # TODO: Save Work Report & Check Majority & Distribute
        # Process goes here

        return data