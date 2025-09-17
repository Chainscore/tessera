import enum
from math import e
from typing import List

from tsrkit_types import TypedArray, Enum

from jam.log_setup import network_logger as logger
from jam.network.base.error import NetworkingErrorCode
from jam.network.connection import NodeConnection
from jam.types import HeaderHash 


from tsrkit_types.integers import U32
from tsrkit_types.struct import structure
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.types.protocol.core import TimeSlot
from jam.utils.constants import GENESIS_HASH


class Direction(Enum):
    AscExc = 0
    DesInc = 1


@structure
class CE128Data:
    header: HeaderHash
    dir: Direction
    max_blocks: U32


class BlockRequest(NetworkProtocol):
    """
    CE 128 Protocol for handling Block requests

    Protocol Flow:
        Node -> Node

        --> Header Hash ++ Direction ++ Maximum Blocks
        --> FIN
        <-- [Block]
        <-- FIN
    Source:
        https://github.com/zdave-parity/jam-np/blob/main/simple.md#ce-128-block-request
    """

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.CE128

    async def transmit(self, data: CE128Data, peers: List[NodeConnection]|None = None):
        """Transmit Block Request"""
        from jam.network.start import node 
        if not node: return

        stream_data = U32(len(data.encode())).encode() + data.encode()
        logger.debug("Transmitting block request to node", num=len(node.connection_ids), max_blocks=data.max_blocks)

        header_hash = data.header.hex()[:16] + "..."
        transmitted_count = 0
        responses = []

        if not peers:
            # If no specific peers are provided, use all connected nodes
            peers = node.all_connected 

        for client in peers:
            try:
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                client.stream_prefix[stream_id] = self._prefix
                client.stream_buffer[stream_id] = b""
                data = await client.close_and_wait(message=stream_data, stream_id=stream_id)

                transmitted_count += 1
                responses.append(data)

                logger.debug(
                    "Block request transmitted",
                    stream_id=stream_id,
                    header_hash=header_hash,
                )
            except Exception as e:
                responses.append(None)
                logger.error("Failed to transmit state request", error=e)

        logger.debug(
            "Block request transmission completed",
            transmitted_to=transmitted_count,
            header_hash=header_hash,
        )

        return responses

    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Process Block Request"""
        buffer = server.stream_buffer[stream_id][1:]

        from jam.settings import settings
        from jam.block.block import Block

        data = CE128Data.decode(buffer[4:])

        logger.debug(
            "Processing block request",
            stream_id=stream_id,
            header_hash=data.header.hex(),
            direction=data.dir,
            max_blocks=data.max_blocks,
        )

        # Get the start block
        start_block = Block.load(data.header, settings.main_db)
        if not start_block:
            logger.info("Block not found", hh=data.header.hex()[:16]+"...")
            server.stream_and_close(b"", stream_id)
            return

        start_timeslot = start_block.header.slot
        if data.dir == Direction.AscExc:
            start_key = Block.get_storage_key_slot(start_timeslot + 1)
            end_key = Block.get_storage_key_slot(TimeSlot(2**32 - 1))
            limit = int(data.max_blocks)
        else:
            start_key = Block.get_storage_key_slot(TimeSlot(0))
            end_key = Block.get_storage_key_slot(start_timeslot)
            limit = 2**32 - 1


        hhs = settings.main_db.get_range(
            start_key, 
            end_key,
            limit=limit
        )

        # If desc, take last max_blocks
        if data.dir == Direction.DesInc:
            hhs = dict(list(hhs.items())[-data.max_blocks:])

        # Get all header hashes in between
        all_blocks = []
        for hh in hhs.values():
            _data = settings.main_db.get(Block.get_storage_key_block(hh))
            if _data:
                all_blocks.append(Block.decode(_data))
            else:
                logger.error("Block not found against recorded header_hash", header_hash=hh.hex())
                break

        if data.dir == Direction.DesInc:
            all_blocks.reverse()

        # It has to be an array and not a vector 
        msg = TypedArray[Block, len(all_blocks)](all_blocks).encode()
        data = U32(len(msg)).encode() + msg
        
        CHUNK_SIZE = 1200 
        offset = 0
        # Manually chunk it up, aioquic twrow invalid payload error 
        while offset < len(data):
            chunk = data[offset: offset+CHUNK_SIZE]
            if len(chunk) < CHUNK_SIZE:
                server.stream_and_close(chunk, stream_id)
            else:
                server.stream_and_keep_open(chunk, stream_id)
            offset += len(chunk)
        
        logger.debug(
            "Blocks request completed successfully. Closed stream",
            stream_id=stream_id,
            len=len(all_blocks),
        )

    def res_intercept(self, stream_id: int, client: NodeConnection):
        """Intercept Acknowledgement"""
        from jam.block.block import Block

        buffer = client.stream_buffer[stream_id]

        logger.debug("Block request ack received", stream_id=stream_id, buffer_size=len(buffer))

        # try:
        b_len = U32.decode(buffer)
        blocks = []
        offset = 0
        while offset < b_len:
            data, off_ = Block.decode_from(buffer[4:], offset)
            offset += off_
            blocks.append(data)
        return blocks 
