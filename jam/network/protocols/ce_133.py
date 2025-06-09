from typing import cast, TYPE_CHECKING
from jam.config.logging import get_logger

if TYPE_CHECKING:
    from jam.network.quic.server import QuicServerProtocol
    from jam.network.node import Node

from tsrkit_types.integers import Uint
from tsrkit_types.struct import structure
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types.work import WorkPackage

# Module-specific logger
logger = get_logger("network")

@structure
class WorkPackageCore:
    work_package : WorkPackage
    core_index : Uint

@structure
class CE133Data:
    package_data: WorkPackageCore
    extrinsics: Uint


class WorkPackageSubmission(NetworkProtocol):
    """
    CE 133 Protocol for submitting Work Package

    Protocol Flow:
        Builder -> Guarantor

        --> Core Index ++ Work-Package
        --> [Extrinsic]
        --> FIN
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-133-work-package-submission
    """


    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE133

    def transmit(self, node: "Node", data: CE133Data):
        """Transmit Work Package from Builder (client) to Guarantor (server)"""

        stream_a = self._prefix.encode() + data.package_data.encode()
        stream_b = data.extrinsics.encode()

        logger.info(
            "Transmitting work package to guarantors",
            node_name=node.name,
            core_index=int(data.package_data.core_index),
            guarantor_count=len(node.connections),
            stream_a_size=len(stream_a),
            stream_b_size=len(stream_b),
            extrinsics_count=int(data.extrinsics)
        )

        transmitted_count = 0
        # TODO: Use Particular Validators' Connections
        for client in node.connections:
            try:
                stream_id = client.stream_and_keep_open(message=stream_a)
                client.stream_and_close(message=stream_b, stream_id=stream_id)
                transmitted_count += 1
                
                logger.debug(
                    "Work package transmitted to guarantor",
                    node_name=node.name,
                    stream_id=stream_id,
                    core_index=int(data.package_data.core_index)
                )
            except Exception as e:
                logger.error(
                    "Failed to transmit work package to guarantor",
                    node_name=node.name,
                    error=str(e),
                    error_type=type(e).__name__
                )
        
        logger.info(
            "Work package transmission completed",
            node_name=node.name,
            transmitted_to=transmitted_count,
            total_guarantors=len(node.connections),
            core_index=int(data.package_data.core_index)
        )

    def server_intercept(self, buffer: bytes, server: "QuicServerProtocol", stream_id: int):
        """Intercept & Process Work Package on Guarantor (server)"""

        try:
            logger.debug(
                "Received work package submission",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )
            
            data, offset = CE133Data.decode_from(buffer)
            data = cast(CE133Data, data)

            logger.info(
                "Processing work package submission",
                stream_id=stream_id,
                core_index=int(data.package_data.core_index),
                extrinsics_count=int(data.extrinsics),
                work_package_hash=hash(str(data.package_data.work_package))  # Simple hash for logging
            )
            
            # TODO: Process received Work Package
            # Process goes here

            logger.info(
                "Work package processed successfully",
                stream_id=stream_id,
                core_index=int(data.package_data.core_index)
            )

            # Return acknowledgment to Builder
            ack = self._prefix.encode() + b""
            server.stream_and_close(stream_id, ack)

            logger.debug(
                "Acknowledgement sent to builder",
                stream_id=stream_id,
                ack_size=len(ack)
            )
            
        except Exception as e:
            logger.error(
                "Error processing work package submission",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )

    def client_intercept(self, buffer: bytes, stream_id: int):
        """Intercept Acknowledgement"""

        logger.info(
            "Work package acknowledgement received",
            stream_id=stream_id,
            buffer_size=len(buffer)
        )


