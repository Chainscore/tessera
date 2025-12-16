from jam.utils.task_utils import create_safe_task
from typing import cast, TYPE_CHECKING

from tsrkit_types import Uint, U32, U8, U64, Bool
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.log_setup import network_logger as logger

from jam.network.connection import NodeConnection
from jam.network.base.protocol import NetworkProtocol, PrefixType

from jam.network.protocols.ce_128 import BlockRequest, CE128Data, Direction
from jam.block import Block, Header

from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import HeaderHash
from jam.types.protocol.validators import ValidatorData
from jam.api.rpc.subscription_handlers import subscribe_sync_status
from jam.telemetry import emit_event
from jam.telemetry.events import (
    BlockAnnouncementStreamOpened, BlockAnnounced, Importing,
    BlockVerified, BlockVerificationFailed, SyncStatusChanged,
    BlockOutline, Bytes32
)
from tsrkit_types import Bytes, Bytes32

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
    _processed_headers: set[HeaderHash] = set()

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
        logger.debug("Handshake started", final=final.header_hash.hex(), slot=final.time_slot, leaves=leaves.to_json())
        conn.stream_and_keep_open(data, stream_id)
    
    @classmethod
    def block_to_announcement(cls, block: Block) -> Announcement:
        """
        Convert a Block to an Announcement.
        """
        from jam.finality.finality import Finality
        from jam.types.protocol.crypto import Hash
        from jam.settings import settings

        finality = Finality()
        final_block = finality.load_final(settings.main_db)
        if not final_block:
            logger.error("No final block found, using genesis block.")
            final_block = Block.genesis()

        header_hash = final_block.header.hash()
        block_slot = final_block.header.slot

        final = Final(header_hash=header_hash, time_slot=block_slot)
        return Announcement(header=block.header, final=final)


    async def transmit(self, announcement: Announcement):
        """Announce Block to Peers (servers)"""
        from jam.network.start import node
        if not node:
            logger.error("Node not found to transmit")
            return

        message = announcement.encode()
        if announcement.header.hash() not in self._processed_headers: 
            logger.info(f"Announcing new block ({announcement.header.hash().hex()[:8]+".."}) to peers")

        announced_count = 0
        chunk = U32(len(message)).encode() + message
        
        # I think we're supposed to emit for each peer seperately, but that's too many events;
        # Maybe once we optimise frontend, we can emit for each peer seperately
        emit_event(BlockAnnounced(
            peer_id=Bytes32(bytes(32)),
            announcer=U8(0),  # 0 = Local
            slot=announcement.header.slot,
            header_hash=Bytes32(announcement.header.hash())
        ))

        for conn in node.active_peers:
            conn.stream_and_keep_open(chunk, conn.up0_stream)
            announced_count += 1
            
            logger.debug(
                "📣 Block announced to peer",
                block_slot=int(announcement.header.slot),
                stream_id=conn.up0_stream,
            )
        logger.debug(
            "Block announcement completed",
            announced_to=announced_count,
            block_slot=int(announcement.header.slot),
        )

    def req_intercept(self, stream_id: int, conn: NodeConnection, data: bytes):
        """Intercepting & Process new blocks from peers."""
        logger.debug("Intercepting UP0 stream", len=len(data), stream_id=stream_id)

        # conn = node._protocols[peer.metadata.port]
        # if node.is_builder and not server.peer_handshake:
        #     up_stream = stream_id
        #     node.peer_conn[peer] = stream_id, conn

        # if stream_id != conn.up0_stream:
        #     logger.warning("UP0 Stream ID updated", stream_id=stream_id, old_stream=conn.up0_stream)
        #     # Update the stream ID
        #     conn.up0_stream = stream_id

        # # Handle handshake message
        # if conn.is_initialized and conn.has_pending_handshake:
        #     # Reverse Handshake on Server
        #     logger.info("Doing reverse handshake")
        #     self.handshake(stream_id, conn)
        #     conn.has_pending_handshake = False


        if not conn.handshake_completed :
            # Parse received Handshake
            h_len= U32.decode(data[0:4])
            if len(data[4:]) != h_len:
                logger.error("Got Handshake with incorrect length", expected=h_len, got=len(data[4:]))
                return 

            h = Handshake.decode(data[4:])

            # TODO: Process Handshake
            logger.debug("Received UP0 handshake", h=h.to_json())

            conn.handshake_completed = True

            if conn.is_initiating:
                self.handshake(stream_id, conn, False)
                conn.up0_stream = stream_id

            # Start synchornization
            create_safe_task(self.synchronise(h), name="up0_sync")

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
            hh = anc.header.hash()
            
            # if we have not already processed this header, announce it 
            if hh not in self._processed_headers:
                self._processed_headers.add(hh)
                # Process goes here
                create_safe_task(self._process_header(anc=anc, node=conn), name="up0_process_header")
            logger.debug(
                "Block announcement 📣 processed successfully", stream_id=stream_id,
                block_slot=int(anc.final.time_slot),
                header_hash=anc.header.hash().hex()[:16] + "...",
                root=anc.header.parent_state_root.hex()[:16] + "..."
            )

    def res_intercept(self, stream_id: int, client):
        raise NotImplementedError("Client Intercept not available for UP protocols")

    async def _process_header(self, anc: Announcement, node: NodeConnection|None = None):
        from jam.state.state import state
        header = anc.header

        logger.debug("Fetching block to import", slot=header.slot)
        create_safe_task(subscribe_sync_status("InProgress"), name="sync_status")
        blocks = await BlockRequest().transmit(
            CE128Data(
                header=HeaderHash(header.hash()),
                dir=Direction.DesInc,
                max_blocks=U32(1),
            ),
            peers=[node] if node else None
        )
        if not blocks or len(blocks) == 0 or blocks[0] is None or len(blocks[0]) == 0 or blocks[0][0] is None:
            if node is None:
                logger.error("No blocks received for header", header=header.hash().hex()[:16] + "...")
                return None
            return await self._process_header(anc, None)

        _valid = state._force_transition(blocks[0][0])
        if _valid:
            create_safe_task(self.transmit(anc), name="up0_transmit")
            create_safe_task(subscribe_sync_status("Completed"), name="sync_status")

    @classmethod
    async def synchronise(cls, h: Handshake):
        from jam.state.state import state
        create_safe_task(subscribe_sync_status( "InProgress"), name="sync_status")

        # To know how many blocks to fetch
        # (h.final.slot - state.tau)
        if h.final.time_slot <= state.tau:
            create_safe_task(subscribe_sync_status("Completed"), name="sync_status")
            return

        data_req = CE128Data(
            header=HeaderHash(h.final.header_hash),
            dir=Direction.DesInc,
            max_blocks=U32(h.final.time_slot - state.tau),
        )

        logger.debug("Requesting Blocks to Sync", num=data_req.max_blocks)
        blocks_to_import = (await BlockRequest().transmit(data_req))[0]
        logger.debug(f"Received {len(blocks_to_import)} blocks. Importing...")

        for block in reversed(blocks_to_import):
            state._force_transition(block)

        logger.info("Sync complete!", state_root=state.root)
        create_safe_task(subscribe_sync_status("Completed"), name="sync_status")
        return
