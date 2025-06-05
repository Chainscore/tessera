from typing import cast
from jam.config.logging import logger
from jam.network.quic.server import QuicServerProtocol
from tsrkit_types.integers import Uint
from tsrkit_types.struct import structure
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.types.work import WorkPackage


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

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE133

    def transmit(self, node: Node, data: CE133Data):
        """Transmit Work Package from Builder (client) to Guarantor (server)"""

        stream_a = self._prefix.encode() + data.package_data.encode()
        stream_b = data.extrinsics.encode()

        logger.info(f"Transmitting Work-Package to {len(node.connections)} Validators")
        # TODO: Use Particular Validators' Connections

        for client in node.connections:
            stream_id = client.stream_and_keep_open(message=stream_a)
            client.stream_and_close(message=stream_b, stream_id=stream_id)

    def server_intercept(self, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """Intercept & Process Work Package on Guarantor (server)"""

        logger.info("Received Work Package")
        data, offset = CE133Data.decode_from(buffer)
        data = cast(CE133Data, data)

        logger.info("Processing Work Package")
        # TODO: Process received Work Package
        # Process goes here

        logger.info(
            f"📩 Processed work package : {data.package_data.work_package} with CI {data.package_data.core_index}"
        )

        # Return acknowledgment to Builder
        ack = self._prefix.encode() + b""
        server.stream_and_close(stream_id, ack)

        logger.info("Sent acknowledgement back to builder")

    def client_intercept(self, buffer: bytes, stream_id: int):
        """Intercept Acknowledgement"""

        logger.info(f"Work Package received on Guarantor Node via stream {stream_id}")


