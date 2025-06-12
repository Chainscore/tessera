from typing import cast

from tsrkit_types import Uint
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.config.logging import logger
from jam.config.settings import settings

from jam.network.base.quic import QuicProtocol
from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.types.block import Block, Header
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import HeaderHash

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

    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.UP0

    @staticmethod
    def handshake(stream_id: int, conn: QuicProtocol):
        from jam.config.settings import settings
        from jam.consensus.grandpa.finality import Finality
        from jam.types.protocol.crypto import Hash

        db = settings.db
        finality = Finality()

        final_block = finality.load_final(db)

        header_hash = Hash.blake2b(final_block.header.encode())
        block_slot = final_block.header.slot

        final = Final(header_hash=header_hash, time_slot=block_slot)

        # TODO: Fetch leaves (descendants of the latest finalized block with no known children)
        leaves = Leaves([])

        handshake = Handshake(final, leaves)
        h_len = Uint[32](len(handshake.encode()))

        # Handshake Message
        conn.stream_and_keep_open(h_len.encode(), stream_id)
        conn.stream_and_keep_open(handshake.encode(), stream_id)

    def transmit(self, node: Node, data: Block):
        """Announce Block to Peers (servers)"""
        from jam.consensus.grandpa.finality import Finality
        from jam.types.protocol.crypto import Hash

        logger.info(f"Announcing blocks to {len(node.peer_conn)} peers.")

        db = settings.db
        finality = Finality()

        final_block = finality.load_final(db)

        header_hash = Hash.blake2b(final_block.header.encode())
        block_slot = final_block.header.slot

        final = Final(header_hash=header_hash, time_slot=block_slot)
        announcement = Announcement(header=data.header, final=final)

        # TODO: Implement actual Block Propagation Grid
        for peer in node.peer_conn:
            up_stream, conn = node.peer_conn[peer]
            conn.stream_and_keep_open(announcement.encode(), up_stream)

    def req_intercept(self, stream_id: int, server: QuicProtocol):
        """Intercepting & Process new blocks from peers."""
        buffer = server.stream_buffer[stream_id]
        peer = server.peer


        logger.info(f"Intercepting UP0 stream (stream {stream_id}).")
        # Process goes here

        up_stream, _ = server.node.peer_conn[peer]
        if stream_id == up_stream:
            # Handle handshake message
            if not server.peer_handshake:
                # Reverse Handshake on Server
                if not server.is_client:
                    self.handshake(stream_id, server)

                # Parse received Handshake
                h_len, _ = Uint[32].decode_from(buffer[stream_id][1:5])

                if len(buffer[stream_id][5:]) == h_len:
                    h, _ = Handshake.decode_from(buffer[stream_id][5:])
                    h = cast(Handshake, h)


                    # TODO: Process Handshake
                    logger.info(f"{server.interface}: Received peer Handshake. {h}")

                    server.stream_buffer[stream_id] = self._prefix.encode()
                    server.peer_handshake = True

            # Handle announcement
            else:
                # Parse received Announcement
                a_len, _ = Uint[32].decode_from(buffer[stream_id][1:5])

                if len(server.stream_buffer[stream_id][5:]) == a_len:
                    a, _ = Announcement.decode_from(server.stream_buffer[stream_id][5:])
                    a = cast(Announcement, a)

                    logger.info(f"Received a new block with header {a.header}. Parent Block: {a.final.header_hash} in T.S {a.final.time_slot}")

                    # TODO: Process new block

                    server.stream_buffer[stream_id] = self._prefix.encode()

        else:
            logger.error(f"{server.interface}: ❌ Different UP Stream.")
            server._quic.close(error_code=0x4, reason_phrase="Multiple UP streams are not allowed.")
            return

    def res_intercept(self, stream_id: int, client: QuicProtocol):
        raise NotImplementedError("Client Intercept not available for UP protocols")



