import json

from typing import cast

from tsrkit_types import TypedVector, Option, Uint, structure, Null

from jam.config.logging import logger
from jam.config.settings import settings
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.quic import QuicProtocol
from jam.storage.item_extrinsics import ItemExtrinsics

from jam.types.protocol.core import CoreIndex
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, Hash
from jam.types.work.package import WorkPackageBundle
from jam.types.work import SegmentRootLookup
from jam.utils.benchmark import benchmark, write_benchmarks_to_txt

from jam.work_package.processor import Processor
from jam.work_package.validator import Validator

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


@structure
class CoreSegment:
    core_index : CoreIndex
    segment_root_map : SegmentRootLookup

@structure
class Credential:
    work_report_hash : WorkReportHash
    ed25519_signature : Ed25519Signature

@structure
class CE134Response:
    len: Uint[32]
    cred: Credential

    @property
    def is_valid(self):
        if len(self.cred.encode()) == self.len:
            return True
        return False


@structure
class CE134Data:
    map_len: Uint[32]
    core_segment: CoreSegment
    bundle_len: Uint[32]
    work_package_bundle : WorkPackageBundle

    @property
    def is_valid(self):
        if (len(self.core_segment.encode()) == self.map_len
                and len(self.work_package_bundle.encode()) == self.bundle_len):
            return True
        return False

OptCred = Option[Credential]

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

        logger.info(f"Transmitting Work-Package-Bundle to {len(node.peer_conn)} Guarantors")
        # TODO: Use Actual Guarantors Connections

        msg_a = data.core_segment.encode()
        len_a = Uint[32](len(msg_a)).encode()
        msg_b = data.work_package_bundle.encode()
        len_b = Uint[32](len(msg_b)).encode()

        responses = TypedVector[Credential]([])
        for peer in node.peer_conn:
            if int(peer.data.metadata.port) == 30335:
                logger.info("sending bundle to 30335")
                client = node.peer_conn[peer][1]

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                client.stream_and_keep_open(message=msg_a, stream_id=stream_id)
                client.stream_and_keep_open(message=len_b, stream_id=stream_id)
                data = await client.close_and_wait(message=msg_b, stream_id=stream_id)

                responses.append(data)

        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept Work Package Bundle & Build Work Report on Core's Guarantors (server)"""
        node = server.node
        buffer = server.stream_buffer[stream_id]

        logger.info("Received Work Package Bundle from OG Guarantor")
        data, offset = CE134Data.decode_from(buffer[1:])
        data = cast(CE134Data, data)

        if not data.is_valid:
            raise NetworkingError(Code.INVALID_DATA)

        bundle = data.work_package_bundle

        logger.info("Validating Work Package..")
        validator = Validator()
        validator.validate_wp(bundle.package)

        db = settings.db
        logger.info("Storing Extrinsics..")
        extrinsics = bundle.extrinsics
        ext_da = ItemExtrinsics(db)
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
            msg_a = cred.encode()
            len_a = Uint[32](len(msg_a)).encode()

            # Send Messages with their lengths
            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_close(msg_a, stream_id)

        write_benchmarks_to_txt("benchmarks/guarantee.txt")

        logger.info("Report's Credential sent back to OG Guarantor")

    def res_intercept(self, stream_id: int, client: QuicProtocol) -> OptCred:
        """Intercept validated Work Report from guarantors"""
        buffer = client.stream_buffer[stream_id]

        try:
            data, offset = CE134Response.decode_from(buffer[1:])
            data = cast(CE134Response, data)
            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            logger.info(f"Report's Credential received on OG guarantor (client) via stream {stream_id}")

            # TODO: Save Work Report & Check Majority & Distribute
            logger.info("Distributing this Work Report after achieving majority")

            return OptCred(data.cred)

        except Exception as e:
            logger.error(Code.BAD_RESPONSE)
            return OptCred(Null)
