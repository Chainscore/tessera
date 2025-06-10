from typing import cast, TYPE_CHECKING

from jam.config.logging import get_logger
from tsrkit_types.struct import structure
from jam.types.block import Block, Header

if TYPE_CHECKING:
    from jam.network.quic.server import QuicServerProtocol
    from jam.network.node import Node

from jam.network.protocols.base import NetworkProtocol, PrefixType

from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import HeaderHash

# Module-specific logger
logger = get_logger("network")

@structure
class Final:
    block_hash: HeaderHash
    time_slot: TimeSlot

@structure
class Announcement:
    header: Header
    final: Final

class BlockAnnouncement(NetworkProtocol):
    """
    UP 0 Protocol for announcing & processing new blocks to peers.

    Protocol Flow:
        Node -> Node

        loop {
            --> Announcement OR <-- Announcement (Either side may send)
        }
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#up-0-block-announcement
    """


    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.UP0

    def transmit(self, node: "Node", data: Block):
        """Announce Block to Peers (servers)"""

        final = Final(block_hash=data.header.parent, time_slot=data.header.slot)
        announcement = Announcement(header=data.header, final=final)
        
        message = self._prefix.encode() + announcement.encode()
        
        logger.info(
            "Announcing new block to peers",
            node_name=node.name,
            block_slot=int(data.header.slot),
            parent_hash=data.header.parent.hex()[:16] + "...",
            peer_count=len(node.peer_conn),
            message_size=len(message)
        )
        
        announced_count = 0
        for conn in node.peer_conn:
            try:
                stream_id, client = node.peer_conn[conn]
                client.stream_and_keep_open(stream_id=stream_id, message=message)
                announced_count += 1
                
                logger.debug(
                    "Block announced to peer",
                    node_name=node.name,
                    peer_endpoint=f"{conn.host}:{conn.port}",
                    stream_id=stream_id,
                    block_slot=int(data.header.slot)
                )
            except Exception as e:
                logger.error(
                    "Failed to announce block to peer",
                    node_name=node.name,
                    peer_endpoint=f"{conn.host}:{conn.port}",
                    error=str(e),
                    error_type=type(e).__name__
                )
        
        logger.info(
            "Block announcement completed",
            node_name=node.name,
            announced_to=announced_count,
            total_peers=len(node.peer_conn),
            block_slot=int(data.header.slot)
        )

    def server_intercept(self, buffer: bytes, server: "QuicServerProtocol", stream_id: int):
        """Intercepting & Process new blocks from peers."""

        try:
            data, offset = Announcement.decode_from(buffer)
            data = cast(Announcement, data)
            
            logger.info(
                "Received block announcement",
                stream_id=stream_id,
                block_slot=int(data.final.time_slot),
                parent_hash=data.final.block_hash.hex()[:16] + "...",
                buffer_size=len(buffer)
            )

            logger.debug(
                "Processing incoming block",
                stream_id=stream_id,
                header_slot=int(data.header.slot),
                parent_hash=data.header.parent.hex()[:16] + "...",
                extrinsic_hash=data.header.extrinsic_hash.hex()[:16] + "..."
            )
            
            # Process new header
            # If it is not in our DB, request [header.slot - latest_timeslot] blocks from peer

            # Process goes here
            
            logger.info(
                "Block announcement processed successfully",
                stream_id=stream_id,
                block_slot=int(data.final.time_slot)
            )
            
        except Exception as e:
            logger.error(
                "Error processing block announcement",
                stream_id=stream_id,
                buffer_size=len(buffer),
                error=str(e),
                error_type=type(e).__name__
            )

    def client_intercept(self, buffer: bytes, stream_id: int):
        logger.debug(
            "Block announcement client intercept",
            stream_id=stream_id,
            buffer_size=len(buffer)
        )




