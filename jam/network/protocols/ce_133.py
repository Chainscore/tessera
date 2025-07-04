from typing import cast
from tsrkit_types import Null, structure, Uint, Bool, TypedVector, Option

from jam.logging import get_logger

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.types.protocol.core import CoreIndex
from jam.types.work.manifest import Extrinsics
from jam.types.work.package import WorkPackage

from jam.utils.benchmark import benchmark, write_benchmarks_to_txt

from jam.work_package.processor import Processor

from jam.work_package.guarantor_assignments import guarantor_assignments

# Module-specific logger
logger = get_logger("network")

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

        ci = data.package_data.core_index

        from jam.state.state import state
        logger.info("Tau", tau=state.tau)
        mapping = guarantor_assignments(state)[ci]

        logger.info(
            "Transmitting work package to guarantors",
            node_name=node.name,
            core_index=int(data.package_data.core_index),
            guarantor_count=len(node.peer_conn),
            stream_a_size=data.package_len,
            stream_b_size=data.extrinsics_len,
            extrinsics_count=len(data.extrinsics)
        )

        transmitted_count = 0
        # TODO: Use Particular Validators' Connections

        responses = TypedVector[OptBool]([])
        try:
            for peer in node.peer_conn:
                if peer.ed_key in mapping:
                    logger.info("Sending package to", port=peer.port)
                    client = node.peer_conn[peer][1]
                    transmitted_count += 1

                    # Send Protocol Prefix
                    stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                    # Append prefix to stream buffer so that we know the stream for handling response
                    client.stream_buffer[stream_id] = self._prefix.encode()

                    # Send Messages with their lengths
                    client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                    client.stream_and_keep_open(message=msg_a, stream_id=stream_id)
                    client.stream_and_keep_open(message=len_b, stream_id=stream_id)
                    res = await client.close_and_wait(message=msg_b, stream_id=stream_id)

                    if not res:
                        responses.append(OptBool(Null))
                    else:
                        responses.append(res)

                    logger.debug(
                        "Work package transmitted to guarantor",
                        node_name=node.name,
                        stream_id=stream_id,
                        core_index=int(data.package_data.core_index)
                    )

                    break

            if transmitted_count == 0:
                raise NetworkingError(Code.NO_PEER_CONN)

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
            total_guarantors=len(node.peer_conn),
            core_index=int(data.package_data.core_index)
        )

        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept & Process Work Package on Guarantor (server)"""
        buffer = server.stream_buffer[stream_id]

        try:
            logger.debug(
                "Received work package submission",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )

            data, offset = CE133Data.decode_from(buffer[1:])
            data = cast(CE133Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            wp = data.package_data.work_package
            ci = data.package_data.core_index

            logger.info(
                "Processing work package submission",
                stream_id=stream_id,
                core_index=int(ci),
                extrinsics_count=len(data.extrinsics),
                work_package_hash=hash(str(wp))  # Simple hash for logging
            )

            # Start Refinement Process
            processor = Processor(server.node)
            with benchmark(f"Work Package processed"):
                wr, wr_hash = processor.process(wp, ci, data.extrinsics)

            write_benchmarks_to_txt("benchmarks/refinement.txt")

            logger.info(
                "Work package processed successfully",
                stream_id=stream_id,
                core_index=int(ci)
            )

            # Return acknowledgment to Builder
            ack = b""
            server.stream_and_close(ack, stream_id)

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

    def res_intercept(self, stream_id: int, client: QuicProtocol) -> OptBool:
        """Intercept Acknowledgement"""
        buffer = client.stream_buffer[stream_id]
        if buffer[1:] == b"":
            logger.info(
                "Work package acknowledgement received",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )
            return OptBool(Bool(True))

        return OptBool(Null)

