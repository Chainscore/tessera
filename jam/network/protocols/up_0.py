from typing import cast

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

        for peer in node.peer_conn:
            up_stream, conn = node.peer_conn[peer]
            conn.stream_and_keep_open(announcement.encode(), up_stream)

    def server_intercept(self, buffer: bytes, stream_id: int, server: QuicProtocol):
        """Intercepting & Process new blocks from peers."""

        data, offset = Announcement.decode_from(buffer)

        data = cast(Announcement, data)
        logger.info(f"Received a new block with header {data.header}. Parent Block: {data.final.header_hash} in T.S {data.final.time_slot}")

        logger.info(f"Processing new block.")
        # TODO: Process new block
        # Process goes here

    def client_intercept(self, buffer: bytes, stream_id: int, client: QuicProtocol):
        ...



