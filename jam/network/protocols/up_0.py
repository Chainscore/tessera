from typing import cast

from jam.config.logging import logger
from jam.network.protocols.base import NetworkProtocol, PrefixType
from jam.network.protocols.types import Final, BlockAnnouncement
from jam.state.state import State

from jam.types import Block

class BlockAnnouncementProtocol(NetworkProtocol):
    from jam.network.node import Node

    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.UP0

    def transmit(self, node: Node, data: Block):
        """
        UP 0 Protocol for announcing new blocks to peers.
        Args:
            node (Node): Node which needs to announce the block
            data (Block): Block to be announced
        """
        logger.info(f"Announcing blocks to {len(node.connections)} peers.")

        final = Final(block_hash=data.header.parent, time_slot=data.header.slot)
        announcement = BlockAnnouncement(header=data.header, final=final)

        for conn in node.peer_conn:
            # Block Announcement
            stream_id, client = node.peer_conn[conn]
            message = self._prefix.encode() + announcement.encode()
            client.stream_and_keep_open(stream_id=stream_id, message=message)

    @classmethod
    def intercept(cls, buffer: bytes) -> BlockAnnouncement:
        """
        UP 0 Protocol for intercepting new blocks from peers.
        Args:
            buffer (bytes): Block Announcement data received
        Returns:
            BlockAnnouncement: Decoded bytes data received
        """
        data, offset = BlockAnnouncement.decode_from(buffer)

        data = cast(BlockAnnouncement, data)
        logger.info(f"Received a new block with header {data.header}. Parent Block: {data.final.block_hash} in T.S {data.final.time_slot}")

        return data

    @classmethod
    def process(cls, data: BlockAnnouncement):
        print("Processing new block.")