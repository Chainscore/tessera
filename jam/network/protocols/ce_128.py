import asyncio
import enum
from math import e
from typing import List

from tsrkit_types import TypedArray, Enum

from jam.log_setup import network_logger as logger, TRACE_LEVEL
from jam.network.base.error import NetworkingErrorCode
from jam.network.connection import NodeConnection
from jam.types import HeaderHash 


from tsrkit_types.integers import U32, U64
from tsrkit_types.struct import structure
from jam.network.base.protocol import NetworkProtocol, PrefixType
from jam.types.protocol.core import TimeSlot
from jam.utils.constants import GENESIS_HASH
from jam.utils.gather import gather_with_exceptions
from jam.telemetry import emit_event
from jam.telemetry.events import (
    SendingBlockRequest, BlockRequestSent, BlockRequestFailed,
    ReceivingBlockRequest, BlockRequestReceived, BlockTransferred,
    BlockOutline, Bytes32
)
from tsrkit_types import U8, String, Bytes, Bytes32


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

    async def transmit(self, data: CE128Data, peers: List[NodeConnection]|None = None, node=None):
        """Transmit Block Request"""
        # from jam.network.start import node (removed)
        if not node: return # We need the node to check connections, or maybe we can derive from peers if present? No, we need local node for all_connected fallback.

        stream_data = U32(len(data.encode())).encode() + data.encode()
        logger.debug("Transmitting block request to node", num=len(node.connection_ids), max_blocks=data.max_blocks)

        header_hash = data.header.hex()[:16] + "..."
        transmitted_count = 0
        tasks = []
        event_id = id(data) & 0xFFFFFFFFFFFFFFFF  # Unique event ID

        if not peers:
            # If no specific peers are provided, use all connected nodes
            peers = node.all_connected 

        for client in peers:
            try:
                # Get peer_id - use connection's peer_id or generate from address
                peer_id_bytes = getattr(client, 'peer_id', bytes(32))
                if not isinstance(peer_id_bytes, bytes) or len(peer_id_bytes) != 32:
                    peer_id_bytes = bytes(32)
                
                # Emit SendingBlockRequest event
                emit_event(SendingBlockRequest(
                    peer_id=Bytes32(peer_id_bytes),
                    header_hash=Bytes32(data.header),
                    direction=U8(0 if data.dir == Direction.AscExc else 1),
                    max_blocks=data.max_blocks
                ))
                
                stream_id = client.stream_and_keep_open(message=self._prefix.encode())
                client.stream_prefix[stream_id] = self._prefix
                client.stream_buffer[stream_id] = b""
                res = client.close_and_wait(message=stream_data, stream_id=stream_id)
                task = asyncio.create_task(res)
                tasks.append(task)

                transmitted_count += 1
                
                # Emit BlockRequestSent event
                emit_event(BlockRequestSent(event_id=U64(event_id)))

                logger.log(TRACE_LEVEL,
                    "Block request transmitted",
                    stream_id=stream_id,
                    header_hash=header_hash,
                )
            except Exception as e:
                # Emit BlockRequestFailed event
                emit_event(BlockRequestFailed(event_id=U64(event_id), reason=String(str(e)[:100])))
                logger.error("Failed to transmit state request", error=e)

        responses = await gather_with_exceptions(tasks)
        logger.debug(
            "Block request transmission completed",
            transmitted_to=transmitted_count,
            header_hash=header_hash,
        )

        return responses

    def req_intercept(self, stream_id: int, server: NodeConnection):
        """Process Block Request"""
        buffer = server.stream_buffer[stream_id][1:]

        try:
             settings = server.node.settings
        except:
             from jam.settings import settings

        from jam.block.block import Block

        # Get peer_id for telemetry
        peer_id_bytes = getattr(server, 'peer_id', bytes(32))
        if not isinstance(peer_id_bytes, bytes) or len(peer_id_bytes) != 32:
            peer_id_bytes = bytes(32)
        
        # Emit ReceivingBlockRequest event
        emit_event(ReceivingBlockRequest(peer_id=Bytes32(peer_id_bytes)))

        data = CE128Data.decode(buffer[4:])
        event_id = id(data) & 0xFFFFFFFFFFFFFFFF

        logger.debug(
            "Processing block request",
            stream_id=stream_id,
            header_hash=data.header.hex(),
            direction=data.dir,
            max_blocks=data.max_blocks,
        )
        
        # Emit BlockRequestReceived event
        emit_event(BlockRequestReceived(
            event_id=U64(event_id),
            header_hash=Bytes32(data.header),
            direction=U8(0 if data.dir == Direction.AscExc else 1),
            max_blocks=data.max_blocks
        ))

        # Get the start block
        start_block = Block.load(data.header, settings.main_db)
        if not start_block:
            logger.debug("Block not found", hh=data.header.hex()[:16]+"...")
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
        
        # Emit BlockTransferred events for each block
        for i, block in enumerate(all_blocks):
            is_last = (i == len(all_blocks) - 1)
            block_outline = BlockOutline(
                size=U32(len(block.encode())),
                header_hash=Bytes32(block.header.hash()),
                num_tickets=U32(len(block.extrinsic.tickets) if hasattr(block.extrinsic, 'tickets') else 0),
                num_preimages=U32(len(block.extrinsic.preimages) if hasattr(block.extrinsic, 'preimages') else 0),
                preimages_size=U32(sum(len(p.encode()) for p in block.extrinsic.preimages) if hasattr(block.extrinsic, 'preimages') else 0),
                num_guarantees=U32(len(block.extrinsic.guarantees) if hasattr(block.extrinsic, 'guarantees') else 0),
                num_assurances=U32(len(block.extrinsic.assurances) if hasattr(block.extrinsic, 'assurances') else 0),
                num_disputes=U32(
                    len(block.extrinsic.disputes.verdicts) + 
                    len(block.extrinsic.disputes.culprits) + 
                    len(block.extrinsic.disputes.faults) if hasattr(block.extrinsic, 'disputes') else 0
                )
            )
            from tsrkit_types import Bool
            emit_event(BlockTransferred(
                event_id=U64(event_id),
                slot=block.header.slot,
                block=block_outline,
                last_block=Bool(is_last)
            ))

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

        logger.log(TRACE_LEVEL, "Block request ack received", stream_id=stream_id, buffer_size=len(buffer))

        # try:
        b_len = U32.decode(buffer)
        blocks = []
        offset = 0
        while offset < b_len:
            data, off_ = Block.decode_from(buffer[4:], offset)
            offset += off_
            blocks.append(data)
        return blocks 
