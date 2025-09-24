from typing import cast

from tsrkit_types import U8
from tsrkit_types.integers import Uint
from tsrkit_types.struct import structure
from jam.logging import get_logger
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.connection import NodeConnection

from jam.storage.da.reports import ReportsDA

from jam.types.protocol.crypto import WorkReportHash, Hash
from jam.types.work.report import WorkReport
from jam.types.work.manifest import Assurers

# Module-specific logger
logger = get_logger("network")


@structure
class CE136Data:
    len: Uint[32]
    work_report_hash: WorkReportHash

    @property
    def is_valid(self):
        if len(self.work_report_hash.encode()) == self.len:
            return True
        return False


@structure
class CE136Response:
    len: Uint[32]
    work_report: WorkReport

    @property
    def is_valid(self):
        if len(self.work_report.encode()) == self.len:
            return True
        return False


class WorkReportRequest(NetworkProtocol):
    """
    CE 136 Protocol for requesting Work Report

    Protocol Flow:
        Node -> Node

        --> Work-Report Hash
        --> FIN
        <-- Work-Report
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-136-work-report-request
    """

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE136

    async def transmit(self, data: CE136Data) -> WorkReport | None:
        """Request Work Report from Node"""

        from jam.network.start import node

        msg_a = data.work_report_hash.encode()
        len_a = data.len.encode()

        logger.info(f"Requesting Work-Report from {len(node.all_connected)} Validators")

        for client in node.all_connected:
            try:
                logger.debug("Requesting report from", peer=client)

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # set prefix and buffer
                client.stream_prefix[stream_id] = U8(self._prefix)
                client.stream_buffer[stream_id] = b""

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                res = await client.close_and_wait(
                    message=msg_a, stream_id=stream_id
                )

                if res is not None:
                    return res
                else:
                        logger.error("Error fetching work report from: ", peer=client)
            except Exception as e:
                logger.error(Code.BAD_RESPONSE, error=str(e))

        return None

    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Intercept & Fetch requested Work Report on Node"""
        buffer = server.stream_buffer[stream_id][1:]

        logger.info("Received Work Report Request")
        try:
            data = CE136Data.decode(buffer)
            data = cast(CE136Data, data)
            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            logger.debug("Fetching Work Report")
            # fetching work report from DA
            from jam.settings import settings

            d3l = settings.d3l
            reports_da = ReportsDA(d3l)
            report = reports_da.get(data.work_report_hash)

            # Return requested report to client node
            msg_a = report.encode()
            len_a = Uint[32](len(msg_a)).encode()

            # Send Messages with their lengths
            server.stream_and_keep_open(len_a, stream_id)
            server.stream_and_close(msg_a, stream_id)

            logger.info(
                f"📩 Processed work report query.",
                report_hash=data.work_report_hash.hex()[:16] + "...",
                peer=server,
            )
        except Exception as e:
            # Stop Streaming
            server.stop_stream(stream_id, 1)

            logger.error(Code.BAD_RESPONSE, error=str(e))

    def res_intercept(self, stream_id: int, client: NodeConnection) -> WorkReport | None:
        """Intercept Requested Work Report"""
        buffer = client.stream_buffer[stream_id]

        try:
            data = CE136Response.decode(buffer)
            data = cast(CE136Response, data)
            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            wr_hash = WorkReportHash(Hash.blake2b(data.work_report.encode()))

            logger.info(
                f"Requested Report received.", peer=client, stream_id=stream_id
            )

            # TODO: Save Work Report
            from jam.settings import settings
            rep_da = ReportsDA(settings.d3l)
            rep_da.put(wr_hash, data.work_report)

            return data.work_report

        except Exception as e:
            logger.error(Code.BAD_RESPONSE, error=str(e))
            return None
