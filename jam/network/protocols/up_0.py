from dataclasses import dataclass
from typing import cast

from jam.config.logging import logger
from jam.network.quic.server import QuicServerProtocol

from jam.types.block import Block
from jam.network.protocols.base import NetworkProtocol, PrefixType

from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.utils.json import JsonSerde

from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import HeaderHash
from jam.types import Header

@decodable_dataclass
@dataclass
class Final(Codable, JsonSerde):
    block_hash: HeaderHash
    time_slot: TimeSlot

@decodable_dataclass
@dataclass
class Announcement(Codable, JsonSerde):
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

        logger.info(f"Announcing blocks to {len(node.connections)} peers.")
        # TODO: Use All Validators Connections

        final = Final(block_hash=data.header.parent, time_slot=data.header.slot)
        announcement = Announcement(header=data.header, final=final)

        message = self._prefix.encode() + announcement.encode()
        for conn in node.peer_conn:
            stream_id, client = node.peer_conn[conn]
            client.stream_and_keep_open(stream_id=stream_id, message=message)

    def server_intercept(self, node: Node, buffer: bytes, server: QuicServerProtocol, stream_id: int):
        """Intercepting & Process new blocks from peers."""

        data, offset = Announcement.decode_from(buffer)

        data = cast(BlockAnnouncement, data)
        logger.info(f"Received a new block with header {data.header}. Parent Block: {data.final.block_hash} in T.S {data.final.time_slot}")

        logger.info(f"Processing new block.")
        # TODO: Process new block
        # Process goes here

    def client_intercept(self, node: Node, buffer: bytes, stream_id: int):
        ...



