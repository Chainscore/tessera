from typing import cast
from tsrkit_types import structure, Bool, U32, U8

from jam.log_setup import network_logger as logger

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.block.extrinsics.tickets import TicketEnvelope
import asyncio
from jam.network.connection import NodeConnection
from jam.utils.constants import TICKET_SUBMISSION_END, GENESIS_TS, EPOCH_LENGTH
from jam.finality.finality import Finality
from jam.utils.gather import gather_with_exceptions

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

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE132

    async def transmit(self, data: CE132Data):
        """Transmit Safrole ticket from Validator to validator"""

        from jam.network.start import node
        if not node: return

        try:
            # check finality using received epoch index
            from jam.settings import settings
            main_db = settings.main_db
            finality_block = Finality.load_final(main_db)
            finality_time_slot = finality_block.header.slot

            expected_epoch_index = finality_time_slot // EPOCH_LENGTH
            received_epoch_index = data.epoch_ticket.epoch_index

            if int(expected_epoch_index) != int(received_epoch_index):
                logger.error("Finality lagging", current=received_epoch_index, final=expected_epoch_index)
                raise ValueError("Finality lagging")

            if finality_time_slot%EPOCH_LENGTH < TICKET_SUBMISSION_END:
                # storing ticket extrinsic
                from jam.block.extrinsics.tickets import ticket_store
                ticket_store.store(data.epoch_ticket.ticket)

            else:
                raise ValueError("Tickets are not allowed after TICKET_SUBMISSION_END")

            stream_data = data.epoch_ticket_len.encode() + data.epoch_ticket.encode()
            tasks = []
            logger.info(f"Transmitting ticket ({data.epoch_ticket.ticket.signature.hex()[:6]+".."}) to proxy")
            for client in node.all_connected:
                logger.debug("Transmitting ticket", client=str(client.port))

                stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                client.stream_prefix[stream_id] = U8(self._prefix)
                client.stream_buffer[stream_id] = b""
                res = client.close_and_wait(message=stream_data, stream_id=stream_id)
                task = asyncio.create_task(res)
                tasks.append(task)

                logger.debug(
                    "Ticket transmitted to validator",
                    client=str(client.port),
                    stream_id=stream_id,
                )

            res = await gather_with_exceptions(tasks)
            logger.debug(
                "Ticket transmission completed",
                node=str(node.port),
            )
            return res

        except Exception as e:
            logger.error(
                "Failed to transmit ticket to validator",
                node=str(node.port),
                error=str(e),
                error_type=type(e).__name__,
            )


    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Intercept & Process ticket"""
        buffer = server.stream_buffer[stream_id][1:]

        try:
            logger.debug(
                "Received ticket",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )

            data = CE132Data.decode(buffer)
            data = cast(CE132Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            # check finality using received epoch index
            from jam.settings import settings
            main_db = settings.main_db
            finality_block = Finality.load_final(main_db)
            finality_time_slot = finality_block.header.slot

            expected_epoch_index = finality_time_slot // EPOCH_LENGTH
            received_epoch_index = data.epoch_ticket.epoch_index

            if int(expected_epoch_index) != int(received_epoch_index):
                logger.error("Finality lagging", current=received_epoch_index, final=expected_epoch_index)
                raise ValueError("Finality lagging")

            # Tickets are not allowed after ticket submission ends
            if finality_time_slot%EPOCH_LENGTH < TICKET_SUBMISSION_END:
                # storing ticket extrinsic
                from jam.block.extrinsics.tickets import ticket_store
                ticket_store.store(data.epoch_ticket.ticket)
            else:
                logger.error("Tickets are not allowed after TICKET_SUBMISSION_END")
                raise ValueError("Tickets are not allowed after TICKET_SUBMISSION_END")

            # Return acknowledgment to validator
            ack = b""
            server.stream_and_close(ack, stream_id)

        except Exception as e:
            server.stop_stream(stream_id, 1)
            logger.error(
                "Error in ticket submission",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__,
            )

    def res_intercept(self, stream_id: int, client: NodeConnection) -> Bool:
        """Intercept Acknowledgement"""
        buffer = client.stream_buffer[stream_id]
        if buffer == b"":
            logger.debug(
                "Ticket acknowledgement received",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )
            return Bool(True)

        return Bool(False)
