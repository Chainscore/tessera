import asyncio
from typing import cast

from typing import Any
from tsrkit_types import structure, Null, bool, U16, Uint, TypedVector, Bits, Bool, Bytes, U8
from jam.types.protocol.core import ValidatorIndex

from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.quic import QuicProtocol
from jam.logging import get_logger

from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature, Hash
from jam.utils.gather import gather_with_exceptions

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code


logger = get_logger("network")

@structure
class Judgment:
    epoch_index: Uint[32]  # mention in networking =>  Epoch Index = u32 (Slot / E)
    validator_index: ValidatorIndex
    validity: U8
    work_report_hash: WorkReportHash
    ed25519_signature: Ed25519Signature

@structure
class CE145Data:
    len_a: Uint[32]
    judgment: Judgment

    @property
    def is_valid(self):
        if len(self.judgment.encode()) == self.len_a:
            return True
        return False


class JudgmentPublication(NetworkProtocol):

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE145

    async def transmit(self, node: Node, data: CE145Data):
        """ Announcement of a judgment for the particular work report"""

        len_a = data.len_a.encode()
        msg_a = data.judgment.encode()

        logger.info(
            f"Transmitting Work-report judgement",
            len=data.len_a,
            judgment=len(data.judgment.encode())
        )

        tasks = []
        responses = []
        transmitted_count = 0

        try:

            for peer in node.peer_conn:
                logger.info(f"Transmitting Judgment announcement to {len(node.peer_conn)} validators ")

                client = node.peer_conn[peer][1]

                # send protocol prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                transmitted_count += 1

                # send message with their length
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)

                res = await client.close_and_wait(message=msg_a, stream_id=stream_id)
                # task = asyncio.create_task(res)
                responses.append(res)

                # responses = await gather_with_exceptions(tasks)

                logger.info(
                    "judgment transmit to validator",
                    stream_id=stream_id,
                    port=peer.port
                )

        except Exception as e:
            logger.error(
                "failed to transmit judgment to other validators",
                error=str(e),
                error_type=type(e).__name__
            )

        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """ Intercept Judgment of assigned Work Reports """

        buffer = server.stream_buffer[stream_id]

        try:
            data, offset = CE145Data.decode_from(buffer[1:])
            data = cast(CE145Data, data)
            print(data)

            logger.debug(
                f"Received judgment from the validator {data.judgment.validator_index}",
                stream_id=stream_id,
                peer=server.peer,
                buffer_size=len(buffer[1:])
            )

            # == == == == == error is heer
            if not data.is_valid:
                raise NetworkingError

            ack = b""
            server.stream_and_close(ack, stream_id)

        except Exception as e:
            server.stop_stream(stream_id, 1)

    def res_intercept(self, stream_id: int, client: "QuicProtocol"):
        buffer = client.stream_buffer[stream_id]

        if buffer[1:] == b"":
            logger.info(
                "Judgment acknowledge received",
                stream_id=stream_id,
                buffer_size=len(buffer)
            )
            return True
        return False