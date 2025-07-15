from typing import cast
from tsrkit_types import structure, Uint, Bool, U32

from jam.logging import get_logger

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.types.protocol.crypto import BandersnatchRingVrfSignature
from jam.block.extrinsics.tickets import TicketEnvelope
from jam.utils.constants import VALIDATOR_COUNT

# Module-specific logger
logger = get_logger("network")

@structure
class EpochTicket:
    epoch_index: U32
    ticket: TicketEnvelope

@structure
class CE131Data:
    epoch_ticket_len: Uint[32]
    epoch_ticket: EpochTicket

    @property
    def is_valid(self):
        if len(self.epoch_ticket.encode()) == self.epoch_ticket_len:
            return True
        return False

class SafroleTicketDistribution(NetworkProtocol):
    """
    CE 131 Protocol for transmitting ticket to proxy validator

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
        self._prefix = PrefixType.CE131

    async def transmit(self, node: Node, data: CE131Data):
        """Transmit Safrole ticket from Validator to Proxy validator"""
        msg_a = data.epoch_ticket_len.encode()
        len_a = data.epoch_ticket.encode()

        # TODO: select proxy validator from next epochs validator list
        signature = data.epoch_ticket.ticket.signature

        proxy_validator_index = int.from_bytes(signature[-4:], 'big') % VALIDATOR_COUNT

        if proxy_validator_index == node.validator_index:
            ...
            # TODO: Transmit using ce_132
        else:
            for peer in node.peer_conn:
                if peer.peer_index == proxy_validator_index:
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
                            "Ticket transmitted to proxy validator",
                            node_name=node.name,
                            stream_id=stream_id,
                        )

                        return res

                    except Exception as e:
                        logger.error(
                            "Failed to transmit ticket to proxy validator",
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

            data, offset = CE131Data.decode_from(buffer[1:])
            data = cast(CE131Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            #TODO: verify the proof and check you are the correct proxy

            #TODO: forward the ticket to all current validators

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
