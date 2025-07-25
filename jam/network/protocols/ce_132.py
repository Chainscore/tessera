import time
import math
from typing import cast
from tsrkit_types import structure, Uint, Bool, U32, U8

from jam.logging import get_logger

from jam.network.base.error import NetworkingError, NetworkingErrorCode as Code
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.block.extrinsics.tickets import TicketEnvelope
import asyncio
from jam.network.connection import NodeConnection
from jam.utils.constants import TICKET_SUBMISSION_END, GENESIS_TS, EPOCH_LENGTH


# Module-specific logger
logger = get_logger("network")

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

async def forwarding(slot, timeslot):
    from jam.operations.ticket_queue import ticket_queue
    print("Ticket queue length", ticket_queue.length())
    if not ticket_queue.is_empty():
        ts = timeslot
        ticket_submission_end = TICKET_SUBMISSION_END // 2
        slots_available = ticket_submission_end - slot
        tickets_per_slot = math.ceil(ticket_queue.length() / slots_available)

        print("Tickets per slot", tickets_per_slot)

        for i in range(tickets_per_slot):
            ticket = ticket_queue.pop()
            CE132 = SafroleTicketDistribution()
            data = CE132Data(epoch_ticket_len=ticket.epoch_ticket_len, epoch_ticket=ticket.epoch_ticket)
            responses = await CE132.transmit(data)
            ts += 1
            curr_time = time.time()
            next_time_slot_time = ts * 6 + GENESIS_TS
            if curr_time < next_time_slot_time:
                await asyncio.sleep(next_time_slot_time - curr_time)

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

    async def transmit(self, data: CE132Data):
        """Transmit Safrole ticket from Validator to validator"""

        from jam.network.start import node
        if not node: return

        curr_time = time.time()
        ts = int((curr_time - GENESIS_TS) // 6)
        current_slot = ts % EPOCH_LENGTH
        if current_slot < TICKET_SUBMISSION_END:
            # storing ticket extrinsic
            print(f"Storing ticket in extrinsic, time_slot={ts}, slot={current_slot}")
            from jam.block.extrinsics.tickets import ticket_store
            ticket_store.store(data.epoch_ticket.ticket)

        stream_data = data.epoch_ticket_len.encode() + data.epoch_ticket.encode()

        tasks = []

        try:
            for client in node.all_connected:
                logger.debug("Sending safrol ticket", client=str(client.port))

                stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                client.stream_prefix[stream_id] = U8(self._prefix)
                client.stream_buffer[stream_id] = b""
                task = client.close_and_wait(message=stream_data, stream_id=stream_id)

                tasks.append(task)

                logger.debug(
                    "Ticket transmitted to validator",
                    client=str(client.port),
                    stream_id=stream_id,
                )

            res = await asyncio.gather(*tasks)
            logger.info(
                "Ticket transmission completed",
                node=str(node.port),
            )

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
                "Received safrol ticket",
                stream_id=stream_id,
                buffer_size=len(buffer),
            )

            data, offset = CE132Data.decode_from(buffer)
            data = cast(CE132Data, data)

            if not data.is_valid:
                raise NetworkingError(Code.INVALID_DATA)

            # TODO: process ticket

            curr_time = time.time()
            ts = int((curr_time - GENESIS_TS) // 6)
            current_slot = ts % EPOCH_LENGTH
            if current_slot < TICKET_SUBMISSION_END:
                print("Received ticket from", server.port)
                # storing ticket extrinsic
                print(f"Storing ticket in extrinsic, time_slot={ts}, slot={current_slot}")
                from jam.block.extrinsics.tickets import ticket_store
                ticket_store.store(data.epoch_ticket.ticket)
            else:
                print(f"Tickets are not allowed after TICKET_SUBMISSION_END, time_slot={ts}, slot={current_slot}")
                logger.debug("Tickets are not allowed after TICKET_SUBMISSION_END")

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

    def res_intercept(self, stream_id: int, client: NodeConnection) -> Bool:
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
