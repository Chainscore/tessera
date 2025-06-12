from typing import cast

from tsrkit_types import Null, Vector, structure, Uint, Bool, TypedVector, Option

from jam.config.logging import logger
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.types.protocol.core import CoreIndex
from jam.types.work.manifest import Extrinsics
from jam.types.work.package import WorkPackage

from jam.utils.benchmark import benchmark, write_benchmarks_to_txt

from jam.work_package.processor import Processor


@structure
class WorkPackageCore:
    work_package : WorkPackage
    core_index : CoreIndex

@structure
class CE133Data:
    package_len: Uint[32]
    package_data: WorkPackageCore
    extrinsics_len: Uint[32]
    extrinsics: Extrinsics

    @property
    def is_valid(self):
        if (len(self.package_data.encode()) == self.package_len
                and len(self.extrinsics.encode()) == self.extrinsics_len):
            return True
        return False

OptBool = Option[Bool]

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

        msg_a = data.package_data.encode()
        len_a = data.package_len.encode()
        msg_b = data.extrinsics.encode()
        len_b = data.extrinsics_len.encode()

        logger.info(f"Transmitting Work-Package to {len(node.peer_conn)} Validators")
        # TODO: Use Particular Validators' Connections

        responses = TypedVector[OptBool]([])
        for peer in node.peer_conn:
            if peer.port == 30333:
                logger.info("sending package to 30333")
                client = node.peer_conn[peer][1]

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                client.stream_and_keep_open(message=msg_a, stream_id=stream_id)
                client.stream_and_keep_open(message=len_b, stream_id=stream_id)
                try:
                    data = await client.close_and_wait(message=msg_b, stream_id=stream_id)
                except Exception as e:
                    print("Couldn't close", e)
                if not data:
                    responses.append(OptBool(Null))
                else:
                    responses.append(data)

        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept & Process Work Package on Guarantor (server)"""
        buffer = server.stream_buffer[stream_id]

        logger.info("Received Work Package")
        data, offset = CE133Data.decode_from(buffer[1:])
        data = cast(CE133Data, data)

        if not data.is_valid:
            raise NetworkingError(Code.INVALID_DATA)

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

    def res_intercept(self, stream_id: int, client: QuicProtocol) -> OptBool:
        """Intercept Acknowledgement"""
        buffer = client.stream_buffer[stream_id]
        if buffer[1:] == b"":
            logger.info(f"Work Package received on Guarantor Node via stream {stream_id}")
            return OptBool(True)

        return OptBool(Null)

