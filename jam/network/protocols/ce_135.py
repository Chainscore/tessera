import asyncio
from typing import cast

from tsrkit_types import U8
from tsrkit_types.struct import structure
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import Uint, U32
from tsrkit_types.sequences import TypedVector
from jam.log_setup import logger
from jam.network.connection import NodeConnection
from jam.block.extrinsics.guarantees import ReportGuarantee
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.utils.gather import gather_with_exceptions

@structure
class CE135Data:
    len: Uint[32]
    guaranteed_wr: ReportGuarantee

    @property
    def is_valid(self):
        if len(self.guaranteed_wr.encode()) == self.len:
            return True
        return False


class WorkReportDistribution(NetworkProtocol):
    """
    CE 135 Protocol for distributing Guaranteed Work Report

    Protocol Flow:
        Guarantor -> Validator

        --> Guaranteed Work-Report
        --> FIN
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-135-work-report-distribution
    """

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE135

    async def transmit(self, data: CE135Data):
        """Transmit Work Report from Guarantor to Other Validators"""
        from jam.network.start import node
        msg_a = data.guaranteed_wr.encode()
        len_a = data.len.encode()

        logger.info(
            f"Transmitting Guaranteed Work-Report to {len(node.all_connected)} Validators"
        )

        tasks = []
        for client in node.all_connected:

            try:
                logger.debug("Transmitting report", peer=client)

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # set prefix and buffer
                client.stream_prefix[stream_id] = U8(self._prefix)
                client.stream_buffer[stream_id] = b""

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                res = client.close_and_wait(message=msg_a, stream_id=stream_id)
                task = asyncio.create_task(res)
                tasks.append(task)
                logger.debug(
                    "Report transmitted to validator",
                    stream_id=stream_id,
                    port=client.port,
                )

            except Exception as e:
                logger.error(
                    "Failed to distribute report.",
                    error=str(e),
                    error_type=type(e).__name__,
                )

        responses = list[bool](await gather_with_exceptions(tasks))

        if responses is not None:
            return responses


    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Intercept & Process Work Report on Validator"""

        buffer = server.stream_buffer[stream_id][1:]

        try:
            logger.info("Received Work Report")
            data = CE135Data.decode(buffer)
            data = cast(CE135Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            # Save Mappings
            from jam.incore.processor import Processor
            Processor.process_guaranteed_report(data.guaranteed_wr)

            # Send Acknowledgement
            ack = b""
            server.stream_and_close(ack, stream_id)

            logger.info("Sent acknowledgement back to guarantor")

        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            logger.error(
                "Error processing report",
                guarantor=server,
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

    def res_intercept(self, stream_id: int, client: NodeConnection) -> bool:
        """Intercept Acknowledgement"""

        buffer = client.stream_buffer[stream_id]

        if buffer == b"":
            logger.info(
                f"Guaranteed Report received on Guarantor Node.", stream_id=stream_id
            )
            return True

        return False

