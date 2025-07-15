from typing import cast
from tsrkit_types import Bool

from jam.logging import get_logger

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.protocols.ce_131 import CE131Data

# Module-specific logger
logger = get_logger("network")

CE132Data = CE131Data

class SafroleTicketDistribution(NetworkProtocol):
    """
    CE 132 Protocol for transmitting ticket to all validator

    Protocol Flow:
        Validator -> Validator

        --> Epoch Index ++ Ticket (Epoch index should identify the epoch that the ticket will be used in)
        --> FIN
        <-- FIN
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#ce-131132-safrole-ticket-distribution
    """

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE132

    async def transmit(self, node: Node, data: CE132Data):
        """Transmit Safrole ticket from Validator to validator"""
        msg_a = data.epoch_ticket_len.encode()
        len_a = data.epoch_ticket.encode()

        for peer in node.peer_conn:
            try:
                logger.debug("Sending safrol ticket", peer=str(peer))
                client = node.peer_conn[peer][1]

                # Send Protocol Prefix
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                # Append prefix to stream buffer so that we know the stream for handling response
                client.stream_buffer[stream_id] = self._prefix.encode()

                # Send Messages with their lengths
                client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                res = await client.stream_and_close(message=msg_a, stream_id=stream_id)

                logger.debug(
                    "Ticket transmitted to validator",
                    node_name=node.name,
                    stream_id=stream_id,
                )

                return res

            except Exception as e:
                logger.error(
                    "Failed to transmit ticket to validator",
                    node_name=node.name,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                return None

        logger.info(
            "Ticket transmission completed",
            node_name=node.name,
            total_guarantors=len(node.peer_conn),
        )


    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercept & Process ticket"""
        buffer = server.stream_buffer[stream_id]

        try:
            logger.debug(
                "Received safrol ticket",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )

            data, offset = CE132Data.decode_from(buffer[1:])
            data = cast(CE132Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            # TODO: process ticket

            # Return acknowledgment to validator
            ack = b""
            server.stream_and_close(ack, stream_id)

        except Exception as e:
            logger.error(
                "Error safrol ticket submission",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

    def res_intercept(self, stream_id: int, client: QuicProtocol) -> Bool:
        """Intercept Acknowledgement"""
        buffer = client.stream_buffer[stream_id]
        if buffer[1:] == b"":
            logger.info(
                "Safrol ticket acknowledgement received",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )
            return Bool(True)

        return Bool(False)
