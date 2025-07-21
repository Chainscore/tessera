from typing import cast
from tsrkit_types import structure, Uint, Bool, U32, U8

from jam.logging import get_logger

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.types.protocol.crypto import BandersnatchRingVrfSignature
from jam.block.extrinsics.tickets import TicketEnvelope
from jam.utils.constants import VALIDATOR_COUNT
from jam.network.protocols.ce_132 import SafroleTicketDistribution, CE132Data
from py_ark_vrf import verify_ring
from jam.utils.constants import X

# Module-specific logger
logger = get_logger("network")

@structure
class EpochTicket:
    epoch_index: U32
    ticket: TicketEnvelope

@structure
class CE131Data:
    epoch_ticket_len: U32
    epoch_ticket: EpochTicket

    @property
    def is_valid(self):
        if U32(len(self.epoch_ticket.encode())) == self.epoch_ticket_len:
            return True
        return False

class SafroleTicketProxyDistribution(NetworkProtocol):
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
        len_a = data.epoch_ticket_len.encode()
        msg_a = data.epoch_ticket.encode()

        # calculate validator index
        signature = data.epoch_ticket.ticket.signature
        proxy_validator_index = Uint.from_bytes(signature[-4:], 'big') % VALIDATOR_COUNT
        print(Uint.from_bytes(signature[-4:], 'big'))
        print("Proxy validator", proxy_validator_index)

        # TODO: select proxy validator from next epochs validator list
        # select validator from next epochs validator list using index
        from jam.state.state import state
        proxy_validator = state.gamma.k[proxy_validator_index]

        print("Proxy validator port", proxy_validator.metadata.port)

        if int(proxy_validator.metadata.port) == int(node.port):
            logger.debug(
                "Proxy validator is same as generator validator, transmitting ticket using CE132",
                node_name=node.name,
            )
            from jam.operations.ticket_queue import ticket_queue
            ticket_queue.push(data.epoch_ticket)

        else:
            for peer in node.peer_conn:
                if int(proxy_validator.metadata.port) == int(peer.port) and int(peer.port) != 40000:
                    try:
                        logger.debug("Sending safrol ticket", peer=str(peer), peer_name=str(peer.name))
                        client = node.peer_conn[peer][1]

                        # Send Protocol Prefix
                        stream_id = client.stream_and_keep_open(message=self._prefix.encode())

                        # Append prefix to stream buffer so that we know the stream for handling response
                        client.stream_buffer[stream_id] = self._prefix.encode()

                        # Send Messages with their lengths
                        client.stream_and_keep_open(message=len_a, stream_id=stream_id)
                        res = await client.close_and_wait(message=msg_a, stream_id=stream_id)

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

            # calculate validator index
            signature = data.epoch_ticket.ticket.signature
            proxy_validator_index = Uint.from_bytes(signature[-4:], 'big') % VALIDATOR_COUNT
            from jam.state.state import state
            proxy_validator = state.gamma.k[proxy_validator_index]

            eta = state.eta[2]
            vals = [k.bandersnatch for k in state.gamma.k]
            attempt = U8(data.epoch_ticket.ticket.attempt)
            ad = b''

            verification = verify_ring(
                X.TICKET.value + eta + bytes([attempt]),
                data.epoch_ticket.ticket.signature,
                vals,
                ad
            )
            print("verification", verification)
            # check if you are supposed to be a proxy and ticket is valid
            if int(proxy_validator.metadata.port) == int(server.node.port) and verification:
                from jam.operations.ticket_queue import ticket_queue
                ticket_queue.push(data)
                print("Ticket queue updated", ticket_queue.length())

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
