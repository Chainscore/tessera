from typing import cast

from jam.config.logging import logger

from jam.types.block import Block
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.network.protocols.types import Final, BlockAnnouncement

class BlockAnnouncementProtocol(NetworkProtocol):
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

        logger.info(f"Announcing blocks to {len(node.connections)} peers.")

        final = Final(block_hash=data.header.parent, time_slot=data.header.slot)
        announcement = BlockAnnouncement(header=data.header, final=final)

        message = self._prefix.encode() + announcement.encode()
        for conn in node.peer_conn:
            stream_id, client = node.peer_conn[conn]
            client.stream_and_keep_open(stream_id=stream_id, message=message)

    @classmethod
    def server_intercept(cls, buffer: bytes) -> BlockAnnouncement:
        """Intercepting & Process new blocks from peers."""

        data, offset = BlockAnnouncement.decode_from(buffer)

        data = cast(BlockAnnouncement, data)
        logger.info(f"Received a new block with header {data.header}. Parent Block: {data.final.block_hash} in T.S {data.final.time_slot}")

        logger.info(f"Processing new block.")
        # TODO: Process new block

        return data

    @classmethod
    def client_intercept(cls, buffer: bytes):
        ...



