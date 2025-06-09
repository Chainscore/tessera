import json

from typing import cast

from tsrkit_types import Vector

from jam.config.logging import logger

from jam.network.quic import QuicServerProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.storage.item_extrinsics import ItemExtrinsics

from jam.types.protocol.core import CoreIndex
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, Hash
from jam.types.work.package import WorkPackageBundle
from jam.types.work.report import SegmentRootLookup
from jam.utils.benchmark import benchmark, write_benchmarks_to_txt

from tsrkit_types.integers import Uint
from tsrkit_types.struct import structure

from jam.work_package.processor import Processor
from jam.work_package.validator import Validator

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


@structure
class CoreSegment:
    core_index : CoreIndex
    length : Uint
    segment_root_map : SegmentRootLookup


@structure
class Credential:
    work_report_hash : WorkReportHash
    ed25519_signature : Ed25519Signature


@structure
class CE134Data:
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
        for peer in node.peer_conn:
            if int(peer.data.metadata.port) == 30335:
                logger.info("sending bundle to 30335")
                client = node.peer_conn[peer][1]
                stream_id = client.stream_and_keep_open(message=stream_a)
                data = await client.stream_and_close(message=stream_b, stream_id=stream_id)
                responses.append(data)

        return responses

    def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """Intercept Work Package Bundle & Build Work Report on Core's Guarantors (server)"""

        logger.info("Received Work Package Bundle from OG Guarantor")
        data, offset = CE134Data.decode_from(buffer)
        data = cast(CE134Data, data)

        bundle = data.work_package_bundle

        logger.info("Validating Work Package..")
        validator = Validator()
        validator.validate_wp(bundle.package)

        logger.info("Storing Extrinsics..")
        extrinsics = bundle.extrinsics
        ext_da = ItemExtrinsics()
        with benchmark(f"Extrinsics stored"):
            ext_da.store_processed(extrinsics)

        logger.info("Building Work Report..")
        # Generating report from work package bundle

        with benchmark(f"Work bundle processed"):
            processor = Processor(node)
            report, report_hash = processor.process_bundle(core=data.core_segment.core_index, bundle=bundle,
                                         sr_lookup=data.core_segment.segment_root_map)

        port = node.port
        my_keys = json.load(open("seeds/keys.json"))[str(port)]
        ed25519_key = Ed25519PrivateKey.from_private_bytes(
            bytes.fromhex(my_keys["ed25519_private"][2:])
        )

        # Build Guarantee
        logger.info("Building Guarantee..")
        with benchmark(f"Guarantee built"):
            payload =  report.core_index.encode() + report.encode()
            guarantee = b"jam_guarantee" + Hash.blake2b(payload).encode()

        # Sign the Guarantee
        logger.info("Signing Guarantee..")
        with benchmark(f"Guarantee signed"):
            sign = Ed25519Signature(ed25519_key.sign(guarantee))

        # Build Credential
        cred = Credential(work_report_hash=report_hash, ed25519_signature=sign)

        # Return Credential to OG Guarantor
        logger.info("Sharing Guarantee..")
        with benchmark(f"Guarantee shared"):
            ack = self._prefix.encode() + cred.encode()
            server.stream_and_close(stream_id, ack)

        write_benchmarks_to_txt("benchmarks/guarantee.txt")

        logger.info("Report's Credential sent back to OG Guarantor")

    def client_intercept(self, node: Node, buffer: bytes, stream_id: int) -> Credential:
        """Intercept validated Work Report from guarantors"""

        logger.info(f"Report's Credential received on OG guarantor (client) via stream {stream_id}")
        data, offset = Credential.decode_from(buffer)
        data = cast(Credential, data)

        logger.info("Distributing this Work Report after achieving majority")
        # TODO: Save Work Report & Check Majority & Distribute
        # Process goes here

        return data