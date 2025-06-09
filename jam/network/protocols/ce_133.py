from dataclasses import dataclass
from typing import cast

from jam.config.logging import logger

from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.types.base.null import Null
from jam.types.base.sequences.vector import Vector
from jam.types.protocol.core import CoreIndex
from jam.types.work.manifest import Extrinsics
from jam.types.work.package import WorkPackage
from jam.utils.benchmark import benchmark, write_benchmarks_to_txt

from jam.utils.json import JsonSerde
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass

from jam.work_package.processor import Processor


@decodable_dataclass
@dataclass
class WorkPackageCore(Codable, JsonSerde):
    work_package : WorkPackage
    core_index : CoreIndex

@decodable_dataclass
@dataclass
class CE133Data(Codable, JsonSerde):
    package_data: WorkPackageCore
    extrinsics: Extrinsics


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

    async def transmit(self, node: Node, data: CE133Data):
        """Transmit Work Package from Builder (client) to Guarantor (server)"""

        stream_a = data.package_data.encode()
        stream_b = data.extrinsics.encode()

        logger.info(f"Transmitting Work-Package to {len(node.connections)} Validators")
        # TODO: Use Particular Validators' Connections

        responses = Vector([])
        for peer in node.peer_conn:
            if peer.data.metadata.port == 30333:
                logger.info("sending package to 30333")
                client = node.peer_conn[peer][1]
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                client.stream_and_keep_open(message=stream_a, stream_id=stream_id)
                data = await client.stream_and_close(message=stream_b, stream_id=stream_id)
                responses.append(data)

        return responses

    def server_intercept(self, buffer: bytes, stream_id: int, server: QuicProtocol):
        """Intercept & Process Work Package on Guarantor (server)"""
        logger.info("Received Work Package")
        data, offset = CE133Data.decode_from(buffer)
        data = cast(CE133Data, data)

        logger.info("Processing Work Package")
        processor = Processor(server.node)

        with benchmark(f"Work Package processed"):
            wr, wr_hash = processor.process(data.package_data.work_package, data.package_data.core_index, data.extrinsics)

        write_benchmarks_to_txt("benchmarks/refinement.txt")

        logger.info(
            f"📩 Processed work package : {data.package_data.work_package} into report {wr} & hash {wr_hash} "
        )

        # Return acknowledgment to Builder
        ack = b""
        server.stream_and_close(ack, stream_id)

        logger.info("Sent acknowledgement back to builder")

    def client_intercept(self, buffer: bytes, stream_id: int, client: QuicProtocol):
        """Intercept Acknowledgement"""

        logger.info(f"Work Package received on Guarantor Node via stream {stream_id}")
        return Null

