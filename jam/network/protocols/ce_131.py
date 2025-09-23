from typing import cast
from tsrkit_types import structure, Uint, Bool, U32, U8

from jam.finality.finality import Finality
from jam.log_setup import network_logger as logger

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.network.connection import NodeConnection
from jam.block.extrinsics.tickets import TicketEnvelope
from jam.utils.constants import VALIDATOR_COUNT, EPOCH_LENGTH
from py_ark_vrf import verify_ring, vrf_output
from jam.utils.constants import X


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

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE131

    async def transmit(self, data: CE131Data):
        """Transmit Safrole ticket from Validator to Proxy validator"""

        from jam.network.start import node
        if not node: return

        stream_data = data.epoch_ticket_len.encode() + data.epoch_ticket.encode()

        # calculate validator index using vrf output of signature
        signature = data.epoch_ticket.ticket.signature
        vrf = vrf_output(signature)
        proxy_validator_index = Uint.from_bytes(vrf[-4:], 'big') % VALIDATOR_COUNT

        # select validator from next epochs validator list using index
        from jam.state.state import state
        proxy_validator = state.gamma.p[proxy_validator_index]

        logger.debug(f"Proxy validator port {proxy_validator.metadata.port}")

        from jam.settings import settings
        if proxy_validator.ed25519 == settings.ed25519_public:
            logger.debug(
                "Proxy validator is same as generator validator, transmitting ticket using CE132",
                node=str(node.port),
            )
            # ticket queue for delayed forwarding
            from jam.operations.ticket_queue import ticket_queue
            ticket_queue.push(data)

        else:
            for client in node.all_connected:
                if proxy_validator.ed25519 == client.ed25519_public:
                    try:
                        logger.debug("Sending safrole ticket", client=str(client.port))

                        stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                        client.stream_prefix[stream_id] = U8(self._prefix)
                        client.stream_buffer[stream_id] = b""
                        res = await client.close_and_wait(message=stream_data, stream_id=stream_id)

                        logger.debug(
                            "Ticket transmitted to proxy validator",
                            client=str(client.port),
                            stream_id=stream_id,
                        )

                        return res

                    except Exception as e:
                        logger.error(
                            "Failed to transmit ticket to proxy validator",
                            node=str(client.port),
                            error=str(e),
                            error_type=type(e).__name__,
                        )

    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Intercept & Process ticket"""
        buffer = server.stream_buffer[stream_id][1:]

        try:
            logger.debug(
                "Received safrole ticket",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )

            data, offset = CE131Data.decode_from(buffer)
            data = cast(CE131Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            # finality check using epoch index
            from jam.settings import settings
            main_db = settings.main_db
            finality_block = Finality.load_final(main_db)
            finality_time_slot = finality_block.header.slot

            expected_epoch_index = finality_time_slot // EPOCH_LENGTH
            received_epoch_index = data.epoch_ticket.epoch_index

            if int(expected_epoch_index) != int(received_epoch_index):
                logger.error("Finality lagging", current=received_epoch_index, final=expected_epoch_index)
                raise ValueError("Finality lagging")

            # calculate validator index using vrf output of signature
            signature = data.epoch_ticket.ticket.signature
            vrf = vrf_output(signature)
            proxy_validator_index = Uint.from_bytes(vrf[-4:], 'big') % VALIDATOR_COUNT

            from jam.state.state import state
            proxy_validator = state.gamma.p[proxy_validator_index]

            # verifying the received ticket
            eta = state.eta[2]
            vals = [k.bandersnatch for k in state.gamma.p]
            attempt = U8(data.epoch_ticket.ticket.attempt)
            ad = b''

            verification = verify_ring(
                X.TICKET.value + eta + bytes([attempt]),
                data.epoch_ticket.ticket.signature,
                vals,
                ad
            )
            # check if you are supposed to be a proxy and ticket is valid
            if proxy_validator.ed25519 == settings.ed25519_public and verification:
                logger.debug(f"Proxy ticket received from {server.port}")
                from jam.operations.ticket_queue import ticket_queue
                ticket_queue.push(data)
                logger.debug(f"Ticket queue updated {ticket_queue.length()}")

            # Return acknowledgment to validator
            ack = b""
            server.stream_and_close(ack, stream_id)


        except Exception as e:
            server.stop_stream(stream_id, 1)
            logger.error(
                "Error safrole ticket submission",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

    def res_intercept(self, stream_id: int, client: NodeConnection) -> Bool:
        """Intercept Acknowledgement"""
        buffer = client.stream_buffer[stream_id]
        if buffer == b"":
            logger.info(
                "Safrole ticket acknowledgement received",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )
            return Bool(True)

        return Bool(False)
