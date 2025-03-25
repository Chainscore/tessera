from dataclasses import dataclass
from typing import cast

from jam.config.logging import logger
from jam.network.node import Node
from jam.network.protocols.base import NetworkProtocol, PrefixType

from jam.types import Block, Header
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import HeaderHash

from jam.utils.codec import Codable
from jam.utils.json import JsonSerde
from jam.utils.codec.decorators import decodable_dataclass


@decodable_dataclass
@dataclass
class Final(Codable, JsonSerde):
    block_hash: HeaderHash
    time_slot: TimeSlot

@decodable_dataclass
@dataclass
class BlockAnnouncement(Codable, JsonSerde):
    header: Header
    final: Final


class BlockAnnouncementProtocol(NetworkProtocol):
    def __init__(self):
        super().__init__()
        self._prefix = PrefixType.UP0

    async def transmit(self, node: Node, data: Block):
        """
        UP 0 Protocol for announcing new blocks to peers.
        Args:
            node (Node): Node which needs to announce the block
            data (Block): Block to be announced
        """
        logger.info(f"Announcing blocks to {len(node.connections)} peers.")

        final = Final(block_hash=data.header.parent, time_slot=data.header.slot)
        announcement = BlockAnnouncement(header=data.header, final=final)

        for client in node.connections:
            # Handshake
            # await client.send_message(bytes(self._prefix) + final.encode())

            # Block Announcement
            await client.send_message(announcement.encode())

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