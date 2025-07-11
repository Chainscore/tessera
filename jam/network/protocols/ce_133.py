import time
from typing import cast

from tsrkit_types import structure, Uint
from jam.logging import get_logger

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.peer import Peer

from jam.types.protocol.core import CoreIndex
from jam.types.work.manifest import Extrinsics
from jam.types.work.package import WorkPackage

from jam.work_package.processor import Processor

from jam.utils.constants import GENESIS_TS
from jam.utils.assignment import assign_guarantors

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

    async def transmit(self, node: Node, data: CE133Data) -> tuple[bool, Peer] | None:
        """Transmit Work Package from Builder to Guarantor"""

        msg_a = data.package_data.encode()
        len_a = data.package_len.encode()
        msg_b = data.extrinsics.encode()
        len_b = data.extrinsics_len.encode()

        ci = data.package_data.core_index

        # Fetch guarantors mapping
        mapping = assign_guarantors()
        guarantors = mapping[0][ci]

        wp_hash = data.package_data.work_package.hash().hex()
        logger.info(
            "Trying transmitting work package",
            core=ci,
            guarantors=guarantors,
            wp_hash=wp_hash[:16]+"...",
            stream_a_size=data.package_len,
            stream_b_size=data.extrinsics_len,
            extrinsics_count=len(data.extrinsics)
        )

        transmitted_to = None
        res = None


        for peer in node.peer_conn:
            try:
                # Hardcoded testo
                # if peer.port != 40000:
                #     continue

                if peer.data not in guarantors:
                    continue

                logger.info("Transmitting package", peer=peer)
                client = node.peer_conn[peer][1]

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                client.stream_and_keep_open(message=msg_a, stream_id=stream_id)
                client.stream_and_keep_open(message=len_b, stream_id=stream_id)
                res = await client.close_and_wait(message=msg_b, stream_id=stream_id)

                logger.debug(
                    "Work package transmitted",
                    stream_id=stream_id,
                    core=ci,
                    guarantor=peer
                )

                if res:
                    transmitted_to = peer
                    break

                logger.debug(
                    "Couldn't transmit package",
                    stream_id=stream_id,
                    core=ci,
                    guarantor=peer
                )

            except Exception as e:
                logger.warning(
                    "Work package transmission failed",
                    guarantor=peer,
                    error=str(e),
                    error_type=type(e).__name__
                )

        if not transmitted_to:
            raise NetworkingError(Code.NO_PEER_CONN)
        else:
            logger.info(
                "Work package transmission completed",
                wp_hash=wp_hash[:16] + "...",
                transmitted_to=transmitted_to,
                core=ci,
            )

        return res

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept & Process Work Package on Guarantor"""

        buffer = server.stream_buffer[stream_id]

        try:
            logger.debug(
                "Received work package submission",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )

            data = CE133Data.decode(buffer[1:])
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
                wp_hash=wp.hash().hex()[:16]+"..."
            )

            # Start Refinement Process
            processor = Processor(server.node)
            wr, wr_hash = processor.process(wp, ci, data.extrinsics)

            logger.info(
                "Work package processed successfully",
                stream_id=stream_id,
                wp_hash=wp.hash().hex()[:16]+"...",
                wr_hash=wr_hash,
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
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            logger.error(
                "Error processing work package submission",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )

    def res_intercept(self, stream_id: int, client: QuicProtocol) -> tuple[(bool | None), Peer]:
        """Intercept Acknowledgement"""

        buffer = client.stream_buffer[stream_id]
        if buffer[1:] == b"":
            logger.info(
                "Work package acknowledgement received",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )
            return True, client.peer

        return None, client.peer

