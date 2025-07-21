import asyncio
from typing import cast, TYPE_CHECKING

from tsrkit_types import Uint, U32
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.logging import get_logger

from jam.network.connection import NodeConnection
from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.network.protocols.ce_128 import BlockRequest, CE128Data, Direction
from jam.block import Block, Header

from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import HeaderHash
from jam.types.protocol.validators import ValidatorData

# Module-specific logger
logger = get_logger("network")


@structure
class Leaf:
    header_hash: HeaderHash
    time_slot: TimeSlot

    def __repr__(self):
        return f"Leaf(header_hash={self.header_hash.hex()[:16]}... , slot={int(self.time_slot)})"


class Leaves(TypedVector[Leaf]):
    def __repr__(self):
        preview_count = 100000
        items = ", ".join(repr(leaf) for leaf in self[:preview_count])
        if len(self) > preview_count:
            items += f", ... + {len(self) - preview_count} more"
        return f"Leaves([{items}])"


class Final(Leaf):
    def __repr__(self):
        return f"Final(header_hash={self.header_hash.hex()[:16]}... , slot={int(self.time_slot)})"


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
    def handshake(stream_id: int, conn: NodeConnection, prefix = False):
        from jam.settings import settings
        from jam.finality.finality import Finality
        from jam.types.protocol.crypto import Hash

        db = settings.main_db
        finality = Finality()
        
        data = b""
        if prefix:
            data += PrefixType.UP0.encode()

        logger.debug("Handshake started")
        try:
            final_block = finality.load_final(db)
        except Exception as e:
            logger.error(f"Error occurred while loading final block {e}")
            final_block = Block.genesis()
        
        if not final_block:
            logger.error("No final block found, using genesis block.")
            final_block = Block.genesis()

        header_hash = Hash.blake2b(final_block.header.encode())
        block_slot = final_block.header.slot

        final = Final(header_hash=header_hash, time_slot=block_slot)

        # TODO: Fetch leaves (descendants of the latest finalized block with no known children)
        leaves = Leaves([])
        handshake = Handshake(final, leaves)
        h = handshake.encode()
        h_len = U32(len(h))
        data += h_len.encode()  
        data += h

        # Handshake Message
        conn.stream_and_keep_open(data, stream_id)

        conn.up0_stream = stream_id

    async def transmit(self, data: Block):
        """Announce Block to Peers (servers)"""
        from jam.finality.finality import Finality
        from jam.types.protocol.crypto import Hash
        from jam.network.start import node

        logger.info(f"Announcing blocks to {len(node.connection_ids)} peers.")
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
            block_slot=int(data.header.slot),
            parent_hash=data.header.parent.hex()[:16] + "...",
            message_size=len(message),
        )

        announced_count = 0
        # TODO: Implement actual Block Propagation Grid
        for conn in node.connection_ids.values():
            try:
                ann_len = U32(len(message))

                conn.stream_and_keep_open(ann_len.encode(), conn.up0_stream)
                conn.stream_and_keep_open(message, conn.up0_stream)
                announced_count += 1

                logger.debug(
                    "📣 Block announced to peer",
                    block_slot=int(data.header.slot),
                    anc=anc
                )
            except Exception as e:
                logger.error(
                    "Failed to announce block to peer",
                    error=str(e),
                    error_type=type(e).__name__,
                )

        # for builder in node.builder_conn:
        #     try:
        #         up_stream = node.builder_conn[builder]
        #         ann_len = U32(len(message))
        #
        #         builder.stream_and_keep_open(ann_len.encode(), up_stream)
        #         builder.stream_and_keep_open(message, up_stream)
        #         announced_count += 1
        #
        #         logger.debug(
        #             "Block announced to builder.",
        #             node_name=node.name,
        #             peer=builder.peer,
        #             stream_id=up_stream,
        #             block_slot=int(data.header.slot),
        #         )
        #     except Exception as e:
        #         logger.error(
        #             "Failed to announce block to builder",
        #             node_name=node.name,
        #             peer=builder.peer,
        #             error=str(e),
        #             error_type=type(e).__name__,
        #         )

        logger.info(
            "Block announcement completed",
            node_name=node.name,
            announced_to=announced_count,
            total_peers=len(node.peer_conn),
            block_slot=int(data.header.slot),
        )

    def req_intercept(self, stream_id: int, conn: NodeConnection, data: bytes):
        """Intercepting & Process new blocks from peers."""
        logger.info("Intercepting UP0 stream", len=len(data), stream_id=stream_id)

        # conn = node._protocols[peer.metadata.port]
        # if node.is_builder and not server.peer_handshake:
        #     up_stream = stream_id
        #     node.peer_conn[peer] = stream_id, conn

        # if stream_id != conn.up0_stream:
        #     logger.warning("UP0 Stream ID updated", stream_id=stream_id, old_stream=conn.up0_stream)
        #     # Update the stream ID
        #     conn.up0_stream = stream_id

        # Handle handshake message
        if conn.is_initialized and conn.has_pending_handshake:
            # Reverse Handshake on Server
            logger.info("Doing reverse handshake")
            self.handshake(stream_id, conn)
            conn.has_pending_handshake = False

        if not conn.received_handshake:
            # Parse received Handshake
            h_len= U32.decode(data[0:4])
            if len(data[4:]) != h_len:
                logger.error(
                    "Received Handshake with incorrect length",
                    expected_length=h_len,
                    received_length=len(data[4:]),
                )
                return 

            h = Handshake.decode(data[4:])

            # TODO: Process Handshake
            logger.info(
                "Received peer handshake",
                stream_id=stream_id,
                handshake=h,
                block_slot=int(h.final.time_slot),
                parent_hash=h.final.header_hash.hex()[:16] + "...",
            )

            conn.received_handshake = True

            # Start synchornization
            # asyncio.create_task(self.synchronise(h, conn))

        # Handle announcement
        else:
            a_len = U32.decode(data[0:4])
            if len(data[4:]) != a_len:
                # TODO: Create a buffer to handle large headers 
                logger.error(
                    "Received Announcement with incorrect length",
                    expected_length=a_len,
                    received_length=len(data[4:]),
                )
                return 

            anc = Announcement.decode(data[4:])
            asyncio.create_task(self._process_header(header=anc.header))
            # Process goes here
            logger.info(
                "Block announcement 📣 processed successfully",
                stream_id=stream_id,
                block_slot=int(anc.final.time_slot),
                parent_hash=anc.final.header_hash.hex()[:16] + "...",
                header_hash=anc.header.hash().hex()[:16] + "...",
                anc=anc 
            )

    def res_intercept(self, stream_id: int, client):
        raise NotImplementedError("Client Intercept not available for UP protocols")

    @classmethod
    async def _process_header(cls, header: Header):
        from jam.state.state import state

        logger.info("Fetching block to import", slot=header.slot)
        blocks = await BlockRequest().transmit(
            CE128Data(
                header=HeaderHash(header.hash()),
                dir=Direction.DesInc,
                max_blocks=U32(1),
            ),
        )
        for block in blocks[0]:
            state.transition(block)
            logger.debug("Imported block", slot=block.header.slot)

    @classmethod
    async def synchronise(cls, h: Handshake, node: NodeConnection):
        from jam.state.state import state

        # To know how many blocks to fetch
        # (h.final.slot - state.tau)
        if h.final.time_slot <= state.tau:
            return

        data_req = CE128Data(
            header=HeaderHash(h.final.header_hash),
            dir=Direction.DesInc,
            max_blocks=U32(h.final.time_slot - state.tau),
        )

        logger.info("Requesting Blocks to Sync", num=data_req.max_blocks)
        blocks_to_import = (await BlockRequest().transmit(data_req))[0]
        logger.debug(f"Received {len(blocks_to_import)} blocks. Importing...")

        for block in reversed(blocks_to_import):
            state.transition(block)
            logger.debug(
                "Imported block",
                header_hash=block.header.hash().hex(),
                slot=block.header.slot,
            )

        logger.info("Sync complete!", state_root=state.root)
        return
