from typing import cast

from tsrkit_types import Vector, Option, Null, Uint, structure

from jam.logging import logger
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code

from jam.network.base.jamnp import JAMNP
from jam.types.protocol.crypto import WorkReportHash
from jam.types.work.report import WorkReport
from jam.utils.dummy.dummy_extrinsics import create_dummy_work_report


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


OptRep = Option[WorkReport]


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

    async def transmit(self, data: CE136Data):
        """Request Work Report from Node (server)"""
        from jam.network.node import node 

        msg_a = data.work_report_hash.encode()
        len_a = data.len.encode()

        logger.info(f"Requesting Work-Report from {len(node._protocols)} Validators")

        # TODO: Use Original Guarantor Connection

        responses = Vector([])
        for client in node._protocols.values():
            if int(client.val.metadata.port) == 40000:
                logger.debug("Requesting report from 40000")

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                data = await client.close_and_wait(message=msg_a, stream_id=stream_id)

                responses.append(data)

        return responses

    def req_intercept(self, stream_id: int, server: JAMNP):
        """Intercept & Fetch requested Work Report on Node (server)"""
        buffer = server.stream_buffer[stream_id]

        logger.info("Received Work Report Request")
        data, offset = CE136Data.decode_from(buffer)
        data = cast(CE136Data, data)

        if not data.is_valid:
            raise NetworkingError(Code.INVALID_DATA)

        logger.debug("Fetching Work Report")
        # TODO: Process received Work Report Query
        report = create_dummy_work_report()

        # Return requested report to client node
        msg_a = report.encode()
        len_a = Uint[32](len(msg_a)).encode()

        # Send Messages with their lengths
        server.stream_and_keep_open(len_a, stream_id)
        server.stream_and_close(msg_a, stream_id)

        logger.info(
            f"📩 Processed work report query.",
            report_hash=data.work_report_hash.hex()[:16] + "...",
            peer=server.peer,
        )

    def res_intercept(self, stream_id: int, client: JAMNP) -> OptRep:
        """Intercept Requested Work Report"""
        buffer = client.stream_buffer[stream_id]

        try:
            data, offset = CE136Response.decode_from(buffer[1:])
            data = cast(CE136Response, data)
            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            logger.info(f"Requested Report received.", peer=client.peer, stream_id=stream_id)

            # TODO: Save Work Report

            return OptRep(data.work_report)

        except Exception as e:
            logger.error(Code.BAD_RESPONSE, error=str(e))
            return OptRep(Null)
