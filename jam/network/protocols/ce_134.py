from typing import cast, TYPE_CHECKING

from jam.config.logging import get_logger
if TYPE_CHECKING:
    from jam.network.quic.server import QuicServerProtocol
    from jam.network.node import Node

from tsrkit_types.integers import Uint
from jam.types.work import WorkPackageBundle
from tsrkit_types.struct import structure
from jam.network.protocols.base import NetworkProtocol, PrefixType

from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature
from jam.types.protocol.core import CoreIndex
from jam.work_package.work_package import SegmentRootLookup

# Module-specific logger
logger = get_logger("network")

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

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE134

    def transmit(self, node: "Node", data: CE134Data):
        """Request Work Report from Node (server)"""

        stream_a = self._prefix.encode() + data.core_segment.encode()
        stream_b = data.work_package_bundle.encode()

        logger.info(
            "Transmitting work package bundle to guarantors",
            node_name=node.name,
            core_index=int(data.core_segment.core_index),
            guarantor_count=len(node.connections),
            stream_a_size=len(stream_a),
            stream_b_size=len(stream_b),
            segment_map_length=int(data.core_segment.length)
        )

        transmitted_count = 0
        # TODO: Use Actual Guarantors Connections
        for client in node.connections:
            try:
                stream_id = client.stream_and_keep_open(message=stream_a)
                client.stream_and_close(message=stream_b, stream_id=stream_id)
                transmitted_count += 1
                
                logger.debug(
                    "Work package bundle transmitted to guarantor",
                    node_name=node.name,
                    stream_id=stream_id,
                    core_index=int(data.core_segment.core_index)
                )
            except Exception as e:
                logger.error(
                    "Failed to transmit work package bundle to guarantor",
                    node_name=node.name,
                    error=str(e),
                    error_type=type(e).__name__
                )
        
        logger.info(
            "Work package bundle transmission completed",
            node_name=node.name,
            transmitted_to=transmitted_count,
            total_guarantors=len(node.connections),
            core_index=int(data.core_segment.core_index)
        )

    def server_intercept(self, buffer: bytes, server: "QuicServerProtocol", stream_id: int):
        """Intercept Work Package Bundle & Build Work Report on Core's Guarantors (server)"""

        try:
            logger.debug(
                "Received work package bundle from OG guarantor",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )
            
            data, offset = CE134Data.decode_from(buffer)
            data = cast(CE134Data, data)

            logger.info(
                "Building work report from package bundle",
                stream_id=stream_id,
                core_index=int(data.core_segment.core_index),
                segment_map_length=int(data.core_segment.length)
            )
            
            # TODO: Process received Work Package Bundle, Build Report & Return Credential if validated
            from jam.utils.dummy.dummy_package import create_dummy_credential
            credential = create_dummy_credential()
            # Process goes here

            logger.info(
                "Work report built successfully",
                stream_id=stream_id,
                core_index=int(data.core_segment.core_index),
                credential_hash=credential.work_report_hash.hex()[:16] + "..."
            )

            # Return Credential to OG Guarantor
            ack = self._prefix.encode() + credential.encode()
            server.stream_and_close(stream_id, ack)

            logger.debug(
                "Report credential sent to OG guarantor",
                stream_id=stream_id,
                credential_size=len(credential.encode())
            )
            
        except Exception as e:
            logger.error(
                "Error processing work package bundle",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )

    def client_intercept(self, buffer: bytes, stream_id: int):
        """Intercept validated Work Report from guarantors"""

        try:
            logger.debug(
                "Received report credential from guarantor",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )
            
            data, offset = Credential.decode_from(buffer)
            data = cast(Credential, data)

            logger.info(
                "Report credential received - checking for majority",
                stream_id=stream_id,
                work_report_hash=data.work_report_hash.hex()[:16] + "...",
                signature_length=len(data.ed25519_signature)
            )
            
            # TODO: Save Work Report & Check Majority & Distribute
            # Process goes here
            
            logger.debug(
                "Report credential processed",
                stream_id=stream_id,
                work_report_hash=data.work_report_hash.hex()[:16] + "..."
            )
        except Exception as e:
            logger.error(
                "Error processing report credential",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )