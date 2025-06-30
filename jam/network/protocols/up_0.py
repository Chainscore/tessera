from typing import cast, TYPE_CHECKING

from tsrkit_types import Uint, U32
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.logging import get_logger

from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType


from jam.network.protocols.ce_128 import BlockRequest
from jam.types.block import Block, Header

if TYPE_CHECKING:
    from jam.network.node import Node

from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import HeaderHash

# Module-specific logger
logger = get_logger("network")

@structure
class Leaf:
    header_hash: HeaderHash
    time_slot: TimeSlot

Leaves = TypedVector[Leaf]

Final = Leaf

@structure
class Handshake:
    final: Final
    leaves: Leaves

@structure
class Announcement:
    header: Header
    final: Final

class BlockAnnouncement(NetworkProtocol):
    """
    UP 0 Protocol for announcing & processing new blocks to peers.

    Protocol Flow:
        Node -> Node

        --> Handshake AND <-- Handshake
        loop {
            --> Announcement OR <-- Announcement (Either side may send)
        }
    Source:
        https://docs.jamcha.in/knowledge/advanced/simple-networking/spec#up-0-block-announcement
    """


    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.UP0

    @staticmethod
    def handshake(stream_id: int, conn: QuicProtocol):
        from jam.settings import settings
        from jam.consensus.grandpa.finality import Finality
        from jam.types.protocol.crypto import Hash

        db = settings.main_db
        finality = Finality()

        logger.debug("Handshake started", peer=conn.peer)
        try:
            final_block = finality.load_final(db)
        except Exception as e:
            logger.error(f"Error occurred while loading final block {e}")
            final_block = Block.genesis()

        header_hash = Hash.blake2b(final_block.header.encode())
        block_slot = final_block.header.slot

        final = Final(header_hash=header_hash, time_slot=block_slot)

        # TODO: Fetch leaves (descendants of the latest finalized block with no known children)
        leaves = Leaves([])
        handshake = Handshake(final, leaves)
        h = handshake.encode()
        h_len = Uint[32](len(h))

        # Handshake Message
        conn.stream_and_keep_open(h_len.encode(), stream_id)
        conn.stream_and_keep_open(h, stream_id)

    async def transmit(self, node: "Node", data: Block):
        """Announce Block to Peers (servers)"""
        from jam.consensus.grandpa.finality import Finality
        from jam.types.protocol.crypto import Hash

        logger.info(f"Announcing blocks to {len(node.peer_conn)} peers.")
        from jam.settings import settings

        db = settings.main_db
        finality = Finality()

        final_block = finality.load_final(db)

        header_hash = Hash.blake2b(final_block.header.encode())
        block_slot = final_block.header.slot

        final = Final(header_hash=header_hash, time_slot=block_slot)
        announcement = Announcement(header=data.header, final=final)

        message = announcement.encode()
        logger.info(
            "Announcing new block to peers",
            node_name=node.name,
            block_slot=int(data.header.slot),
            parent_hash=data.header.parent.hex()[:16] + "...",
            peer_count=len(node.peer_conn),
            message_size=len(message)
        )

        announced_count = 0
        # TODO: Implement actual Block Propagation Grid
        for peer in node.peer_conn:
            try:
                up_stream, conn = node.peer_conn[peer]
                ann_len = U32(len(message))

                conn.stream_and_keep_open(ann_len.encode(), up_stream)
                conn.stream_and_keep_open(message, up_stream)
                announced_count += 1

                logger.debug(
                    "Block announced to peer",
                    node_name=node.name,
                    peer=str(peer),
                    stream_id=up_stream,
                    block_slot=int(data.header.slot)
                )
            except Exception as e:
                logger.error(
                    "Failed to announce block to peer",
                    node_name=node.name,
                    peer=str(peer),
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

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercepting & Process new blocks from peers."""
        buffer = server.stream_buffer[stream_id]
        peer = server.peer


        logger.info(
            "Intercepting UP0 stream",
            peer=peer,
            stream_id=stream_id,
        )

        up_stream, _ = server.node.peer_conn[peer]
        if stream_id == up_stream:
            # Handle handshake message
            if not server.peer_handshake:
                # Reverse Handshake on Server
                if not server.is_client:
                    logger.info(
                        "Doing reverse handshake",
                        peer=str(server.peer),
                        interface=server.interface
                    )
                    self.handshake(stream_id, server)

                # Parse received Handshake
                h_len, _ = Uint[32].decode_from(buffer[1:5])

                if len(buffer[5:]) == h_len:
                    h, _ = Handshake.decode_from(buffer[5:])
                    h = cast(Handshake, h)


                    # TODO: Process Handshake
                    logger.info(
                        "Received peer handshake",
                        stream_id=stream_id,
                        peer=str(server.peer),
                        handshake=h,
                        block_slot=int(h.final.time_slot),
                        parent_hash=h.final.header_hash.hex()[:16] + "...",
                        buffer_size=len(buffer),
                        interface=server.interface
                    )

                    server.stream_buffer[stream_id] = self._prefix.encode()
                    server.peer_handshake = True

            # Handle announcement
            else:
                # Parse received Announcement
                a_len, _ = Uint[32].decode_from(buffer[1:5])

                if len(buffer[5:]) == a_len:
                    a, _ = Announcement.decode_from(buffer[5:])
                    a = cast(Announcement, a)

                    logger.info(
                        "Received block announcement",
                        stream_id=stream_id,
                        peer=str(server.peer),
                        block_slot=int(a.final.time_slot),
                        parent_hash=a.final.header_hash.hex()[:16] + "...",
                        buffer_size=len(buffer)
                    )

                    logger.debug(
                        "Processing incoming block",
                        stream_id=stream_id,
                        peer=str(server.peer),
                        header_slot=int(a.header.slot),
                        parent_hash=a.header.parent.hex()[:16] + "...",
                        extrinsic_hash=a.header.extrinsic_hash.hex()[:16] + "..."
                    )

                    logger.info(
                        f"Processed a new block with header {str(a.header)}.",
                        peer=str(server.peer),
                        parent_block=a.final.header_hash,
                        parent_time_slot=a.final.time_slot
                    )

                    server.stream_buffer[stream_id] = self._prefix.encode()

                    # TODO: Process new block
                    # Process new header
                    # If it is not in our DB, request [header.slot - latest_timeslot] blocks from peer
                    # logger.debug("Received header, requesting its full block...", slot=data.header.slot)

                    # BlockRequest().transmit()

                    # Process goes here

                    logger.info(
                        "Block announcement processed successfully",
                        stream_id=stream_id,
                        peer=str(server.peer),
                        block_slot=int(a.final.time_slot)
                    )


        else:
            logger.error(f"{server.interface}: ❌ Different UP Stream.")
            server._quic.close(error_code=0x4, reason_phrase="Multiple UP streams are not allowed.")
            return

    def res_intercept(self, stream_id: int, client: QuicProtocol):
        raise NotImplementedError("Client Intercept not available for UP protocols")



