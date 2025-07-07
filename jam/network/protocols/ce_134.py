from typing import cast, TYPE_CHECKING, Tuple
from tsrkit_types import TypedVector, Option, Uint, structure, Null, U32

if TYPE_CHECKING:
    from jam.network.node import Node

from jam.logging import get_logger

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

from jam.work_package.guarantor_assignments import guarantor_assignments
import asyncio
from jam.types.protocol.core import ValidatorIndex

# Module-specific logger
logger = get_logger("network")

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

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE134

    async def transmit(self, node: "Node", data: CE134Data):
        """Request Work Report from Node (server)"""

        msg_a = data.core_segment.encode()
        len_a = data.map_len.encode()
        msg_b = data.work_package_bundle.encode()
        len_b = data.bundle_len.encode()

        ci = data.core_segment.core_index

        from jam.state.state import state
        logger.info("Tau", tau=state.tau)
        mapping = guarantor_assignments(state)[ci]

        logger.info(
            "Transmitting work package bundle to guarantors",
            node_name=node.name,
            core_index=int(data.core_segment.core_index),
            guarantor_count=len(node.peer_conn),
            stream_a_size=data.map_len,
            stream_b_size=data.bundle_len,
            segment_map_length=len(data.core_segment.segment_root_map)
        )

        transmitted_count = 0
        responses = []
        # TODO: Use Actual Guarantors Connections
        tasks = []
        try:
            for peer in node.peer_conn:
                if peer.ed_key in mapping:
                    logger.debug("Sending bundle to", port=peer.port)
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

                    logger.debug(
                        "Work package bundle transmitted to guarantor",
                        node_name=node.name,
                        stream_id=stream_id,
                        port=peer.port,
                        core_index=int(data.core_segment.core_index)
                    )

            if transmitted_count > 2:
                raise ValueError("Trying to transmit work package bundle to more than 2 guarantors")

            responses = await asyncio.gather(*tasks)

            logger.info(
                "Work package bundle transmission completed",
                node_name=node.name,
                transmitted_to=transmitted_count,
                total_guarantors=len(node.peer_conn),
                core_index=int(data.core_segment.core_index)
            )

        except Exception as e:
            logger.error(
                "Failed to transmit work package bundle to guarantor",
                node_name=node.name,
                error=str(e),
                error_type=type(e).__name__
            )

        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept Work Package Bundle & Build Work Report on Core's Guarantors (server)"""
        from jam.settings import settings
        node = server.node
        buffer = server.stream_buffer[stream_id]

        try:
            logger.debug(
                "Received work package bundle from OG guarantor",
                stream_id=stream_id,
                buffer_size=len(buffer[1:])
            )
            data, offset = CE134Data.decode_from(buffer[1:])
            data = cast(CE134Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            bundle = data.work_package_bundle

            logger.info("Validating Work Package..")
            validator = Validator()
            validator.validate_wp(bundle.package)

            db = settings.main_db
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

            ed25519_key = node.ed_pvt_key

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

            logger.debug(
                "Report credential sent to OG guarantor",
                from_guarantor=server.node.port,
                stream_id=stream_id,
                credential_size=len(cred.encode())
            )

        except Exception as e:
            msg_a = Null.encode()
            len_a = Uint[32](len(msg_a)).encode()

            # Send response
            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_close(msg_a, stream_id)

            logger.error(
                "Error processing work package bundle",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )

    def res_intercept(self, stream_id: int, client: QuicProtocol) -> Tuple[OptCred, ValidatorIndex]:
        """Intercept validated Work Report from guarantors"""
        buffer = client.stream_buffer[stream_id]

        try:
            logger.debug(
                "Received report credential from guarantor",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )

            data, offset = CE134Response.decode_from(buffer[1:])
            data = cast(CE134Response, data)
            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            logger.info(
                "Report credential received - checking for majority",
                stream_id=stream_id,
                work_report_hash=data.cred.work_report_hash.hex()[:16] + "...",
                signature_length=len(data.cred.work_report_hash)
            )

            # TODO: Save Work Report & Check Majority & Distribute
            logger.info("Distributing this Work Report after achieving majority")
            logger.debug(
                "Report credential processed",
                stream_id=stream_id,
                work_report_hash=data.cred.work_report_hash.hex()[:16] + "..."
            )
            return OptCred(data.cred), ValidatorIndex(client.peer.peer_index)

        except Exception as e:
            logger.error(
                Code.BAD_RESPONSE,
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )
            return OptCred(Null)
