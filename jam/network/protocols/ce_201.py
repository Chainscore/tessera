from typing import cast

from tsrkit_types import Vector, Null, Uint, structure, Bytes

from jam.logging import logger

from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code


@structure
class CE201Data:
    len: Uint[32]
    data: Bytes

    @property
    def is_valid(self):
        if len(self.data.encode()) == self.len:
            return True
        return False


class GhostProtocol(NetworkProtocol):
    """
    Test Protocol for transmission of any string data

    Protocol Flow:
        Node -> Node

        --> Data
        --> FIN
        <-- Data
        <-- FIN
    Source:
        Batman
    """

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE201

    async def transmit(self, node: Node, data: str):
        """Request Work Report from Node (server)"""

        msg_a = Bytes(data, "utf-8").encode()
        len_a = Uint[32](len(msg_a)).encode()

        logger.info(f"GHOST - Transmitting to {len(node.peer_conn)} Validators", protocol="201")

        # TODO: Use Original Guarantor Connection

        responses = Vector([])
        for peer in node.peer_conn:
            logger.debug(f"Transmitting data {msg_a.hex()} to {str(peer)}")
            client = node.peer_conn[peer][1]

            # Send Protocol Prefix
            stream_id = client.stream_and_keep_open(message=self._prefix.encode())

            # Append prefix to stream buffer so that we know the stream for handling response
            client.stream_buffer[stream_id] = self._prefix.encode()

            # Send Messages with their lengths
            client.stream_and_keep_open(message=len_a, stream_id=stream_id)
            data = await client.close_and_wait(message=msg_a, stream_id=stream_id)

            responses.append(data)

        return responses

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept & Process test query"""
        buffer = server.stream_buffer[stream_id]

        logger.info("Received Test Request")
        data, offset = CE201Data.decode_from(buffer[1:])
        data = cast(CE201Data, data)

        if not data.is_valid:
            raise NetworkingError(Code.INVALID_DATA)

        message = data.data.decode("utf-8")
        logger.debug(f"Intercepted data {message}")

        # Return requested report to client node
        msg_a = Bytes(f"DATA RECEIVED: {message}", "utf-8").encode()
        len_a = Uint[32](len(msg_a)).encode()

        # Send Messages with their lengths
        server.stream_and_keep_open(len_a, stream_id)
        server.stream_and_close(msg_a, stream_id)

        logger.info(f"📩 Processed Test Protocol query.", message=message, peer=server.peer)

    def res_intercept(self, stream_id: int, client: QuicProtocol) -> str:
        """Intercept Test Response"""
        buffer = client.stream_buffer[stream_id]

        try:
            data, offset = CE201Data.decode_from(buffer[1:])
            data = cast(CE201Data, data)
            if not data or not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            message = data.data.decode("utf-8")
            logger.info(
                f"Test Response received.",
                peer=client.peer,
                stream_id=stream_id,
                message=message,
            )

            return message

        except Exception as e:
            logger.error(Code.BAD_RESPONSE, error=str(e))
            return Null
