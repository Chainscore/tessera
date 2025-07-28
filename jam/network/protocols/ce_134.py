import asyncio
import time

from typing import cast, TYPE_CHECKING

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tsrkit_types import Option, Uint, structure

from jam.logging import get_logger

from jam.network.base.quic import QuicProtocol
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.peer import Peer

from jam.storage.item_extrinsics import ItemExtrinsics

from jam.types.protocol.core import CoreIndex
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature
from jam.types.work.package import WorkPackageBundle
from jam.types.work import SegmentRootLookup

from jam.utils.gather import gather_with_exceptions
from jam.utils.constants import SIGNING_CONTEXTS

# Module-specific logger
logger = get_logger("network")

if TYPE_CHECKING:
    from jam.network.node import Node


@structure
class CoreSegment:
    core_index: CoreIndex
    segment_root_map: SegmentRootLookup


@structure
class Credential:
    work_report_hash: WorkReportHash
    ed25519_signature: Ed25519Signature

    def __repr__(self):
        return f"Credential(wr_hash={self.work_report_hash.hex()}, sign={self.ed25519_signature.hex()[:16]}...)"


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
    work_package_bundle: WorkPackageBundle

    @property
    def is_valid(self):
        if (
            len(self.core_segment.encode()) == self.map_len
            and len(self.work_package_bundle.encode()) == self.bundle_len
        ):
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

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE134

    async def transmit(self, node: "Node", data: CE134Data):
        """Request Work Report from Node"""

        msg_a = data.core_segment.encode()
        len_a = data.map_len.encode()
        msg_b = data.work_package_bundle.encode()
        len_b = data.bundle_len.encode()

        ci = data.core_segment.core_index

        # Fetch guarantors mapping
        from jam.utils.assignment import assign_guarantors

        mapping = assign_guarantors()
        guarantors = mapping[0][ci]

        logger.info(
            "Transmitting work package bundle to guarantors",
            core=ci,
            guarantors=guarantors,
            stream_a_size=data.map_len,
            stream_b_size=data.bundle_len,
            segment_map_length=len(data.core_segment.segment_root_map),
        )

        tasks = []
        responses = []
        transmitted_count = 0

        try:
            for peer in node.peer_conn:
                # For hardcoded testing
                # if peer.port != 40000:
                #     continue

                if peer.data not in guarantors:
                    continue

                logger.debug("Transmitting bundle", peer=peer)
                client = node.peer_conn[peer][1]

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                transmitted_count += 1

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                client.stream_and_keep_open(message=msg_a, stream_id=stream_id)
                client.stream_and_keep_open(message=len_b, stream_id=stream_id)
                res = client.close_and_wait(message=msg_b, stream_id=stream_id)
                task = asyncio.create_task(res)
                tasks.append(task)

                logger.info(
                    "Work package bundle transmitted to guarantor",
                    stream_id=stream_id,
                    peer=peer,
                    core=ci,
                )

            if transmitted_count > 2:
                raise ValueError(
                    "Trying to transmit work package bundle to more than 2 guarantors"
                )

            responses = await gather_with_exceptions(tasks)

            logger.info(
                "Work package bundle transmission completed",
                transmitted_to=transmitted_count,
                guarantors=guarantors,
                core=ci,
            )

        except Exception as e:
            logger.error(
                "Failed to transmit work package bundle to guarantor",
                error=str(e),
                error_type=type(e).__name__,
            )

        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept Work Package Bundle & Build Work Report on Core's Guarantors"""

        from jam.settings import settings

        node = server.node
        buffer = server.stream_buffer[stream_id]

        try:
            logger.debug(
                "Received work package bundle",
                stream_id=stream_id,
                peer=server.peer,
                buffer_size=len(buffer[1:]),
            )

            data = CE134Data.decode(buffer[1:])
            data = cast(CE134Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            bundle = data.work_package_bundle

            logger.debug("Validating Work Package..")
            from jam.incore.validator import Validator

            validator = Validator()
            validator.validate_wp(bundle.package)

            db = settings.main_db
            logger.debug("Storing Extrinsics..")
            extrinsics = bundle.extrinsics
            ext_da = ItemExtrinsics(db)
            ext_da.store_processed(extrinsics)

            # Generating report from work package bundle
            logger.debug("Building Work Report..")
            from jam.incore.processor import Processor

            processor = Processor()
            wr, wr_hash = processor.process_bundle(
                core=data.core_segment.core_index,
                bundle=bundle,
                sr_lookup=data.core_segment.segment_root_map,
            )

            ed25519_key = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private)

            # Build Guarantee
            logger.debug("Building guarantee..")
            payload = SIGNING_CONTEXTS["guarantee"] + wr_hash.encode()

            # Sign the Guarantee
            logger.debug("Signing guarantee..")
            sign = Ed25519Signature(ed25519_key.sign(payload))

            # Build Credential
            cred = Credential(work_report_hash=wr_hash, ed25519_signature=sign)

            # Return Credential to OG Guarantor

            logger.debug(
                "Sharing guarantee..",
                wr_hash=wr_hash.hex()[:16] + "...",
                sign=sign.hex()[:16] + "...",
                to=server.peer,
            )
            msg_a = cred.encode()
            len_a = Uint[32](len(msg_a)).encode()

            # Send Messages with their lengths
            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_close(msg_a, stream_id)

            logger.info(
                "Report credential sent to OG guarantor",
                guarantor=server.peer,
                stream_id=stream_id,
                credential_size=len(cred.encode()),
            )

        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            logger.error(
                "Error processing work package bundle",
                guarantor=server.peer,
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

    def res_intercept(
        self, stream_id: int, client: QuicProtocol
    ) -> tuple[Credential | None, Peer]:
        """Intercept Report Guarantee from guarantors"""

        buffer = client.stream_buffer[stream_id]

        try:
            logger.debug(
                "Received report credential from guarantor",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )

            data = CE134Response.decode(buffer[1:])
            data = cast(CE134Response, data)
            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            logger.info(
                "[EXTRINSICS]: RECEIVED GUARANTEE",
                stream_id=stream_id,
                peer=client.peer,
                wr_hash=data.cred.work_report_hash.hex()[:16] + "...",
                sign=data.cred.ed25519_signature.hex()[:16] + "...",
            )

            return data.cred, client.peer

        except Exception as e:
            logger.error(
                Code.BAD_RESPONSE,
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

            return None, client.peer
