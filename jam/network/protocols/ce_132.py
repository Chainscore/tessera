import asyncio
from typing import cast, TYPE_CHECKING
from tsrkit_types import structure, Bool, U32, U8

from jam.state.transitions import SafroleError, SafroleErrorCode
from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.block.extrinsics.tickets import TicketEnvelope
from jam.utils.constants import TICKET_SUBMISSION_END, EPOCH_LENGTH
from jam.utils.gather import gather_with_exceptions

if TYPE_CHECKING:
    from jam.network.connection import PeerConnection


@structure
class EpochTicket:
    epoch_index: U32
    ticket: TicketEnvelope

@structure
class CE132Data:
    epoch_ticket_len: U32
    epoch_ticket: EpochTicket

    @property
    def is_valid(self):
        if len(self.epoch_ticket.encode()) == self.epoch_ticket_len:
            return True
        return False

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

    _prefix = PrefixType.CE132


    async def transmit(self, data: CE132Data):
        """Transmit Safrole ticket from Validator to validator"""

        node = self.jam.router.node
        if not node: return

        try:
            # check finality using received epoch index
            grandpa = self.jam.grandpa

            finality_block = grandpa.load_final()
            finality_time_slot = finality_block.header.slot

            expected_epoch_index = finality_time_slot // EPOCH_LENGTH
            received_epoch_index = data.epoch_ticket.epoch_index

            if int(expected_epoch_index) != int(received_epoch_index):
                self.logger.error(
                    "Finality lagging",
                    current=received_epoch_index,
                    final=expected_epoch_index
                )
                raise NetworkingError(Code.SYNC_ERROR)

            if finality_time_slot % EPOCH_LENGTH < TICKET_SUBMISSION_END:
                # storing ticket extrinsic
                self.pool.tickets.store(data.epoch_ticket.ticket)

            else:
                self.logger.error("Tickets are not allowed after TICKET_SUBMISSION_END")
                raise SafroleError(
                    SafroleErrorCode.UNEXPECTED_TICKET,
                    "Tickets are not allowed after TICKET_SUBMISSION_END",
                )

            stream_data = data.epoch_ticket_len.encode() + data.epoch_ticket.encode()
            tasks = []
            self.logger.debug(f"Transmitting ticket ({data.epoch_ticket.ticket.signature.hex()[:6]+".."}) to proxy")

            for client in node.all_connected:
                self.logger.trace("Transmitting ticket", client=str(client.port))

                stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                client.stream_prefix[stream_id] = U8(self._prefix)
                client.stream_buffer[stream_id] = b""
                res = client.close_and_wait(message=stream_data, stream_id=stream_id)
                task = asyncio.create_task(res)
                tasks.append(task)

                self.logger.debug(
                    "Ticket transmitted to validator",
                    client=client.peer_id,
                    stream_id=stream_id,
                )

            res = await gather_with_exceptions(tasks)
            self.logger.info(
                "Ticket transmission completed",
                ticket=data.epoch_ticket.ticket.signature.hex()[:6]+"..",
            )

            return res

        except Exception as e:
            self.logger.error(
                "Failed to transmit ticket to validator",
                node=str(node.port),
                error=str(e),
                error_type=type(e).__name__,
            )


    async def req_intercept(self, stream_id: int, server: "PeerConnection"):
        """Intercept & Process ticket"""
        buffer = server.stream_buffer[stream_id][1:]

        try:
            self.logger.debug(
                "Received ticket",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )

            data = CE132Data.decode(buffer)
            data = cast(CE132Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            # check finality using received epoch index
            grandpa = self.jam.grandpa

            finality_block = grandpa.load_final()
            finality_time_slot = finality_block.header.slot

            expected_epoch_index = finality_time_slot // EPOCH_LENGTH
            received_epoch_index = data.epoch_ticket.epoch_index

            if int(expected_epoch_index) != int(received_epoch_index):
                self.logger.error(
                    "Finality lagging",
                    current=received_epoch_index,
                    final=expected_epoch_index
                )
                raise NetworkingError(Code.SYNC_ERROR)

            # Tickets are not allowed after ticket submission ends
            if finality_time_slot % EPOCH_LENGTH < TICKET_SUBMISSION_END:
                # storing ticket extrinsic
                self.pool.tickets.store(data.epoch_ticket.ticket)

                self.logger.info(
                    "Received ticket.",
                    ticket=data.epoch_ticket.ticket.signature.hex()[:6] + "..",
                )

            else:
                self.logger.error("Tickets are not allowed after TICKET_SUBMISSION_END")
                raise SafroleError(
                    SafroleErrorCode.UNEXPECTED_TICKET,
                    "Tickets are not allowed after TICKET_SUBMISSION_END",
                )

            # Return acknowledgment to validator
            ack = b""
            server.stream_and_close(ack, stream_id)

        except Exception as e:
            server.stop_stream(stream_id, 1)
            self.logger.error(
                "Error in ticket submission",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

    async def res_intercept(self, stream_id: int, client: "PeerConnection") -> Bool:
        """Intercept Acknowledgement"""
        buffer = client.stream_buffer[stream_id]

        if buffer == b"":
            self.logger.debug(
                "Ticket acknowledgement received",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )
            return Bool(True)

        return Bool(False)
