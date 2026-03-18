from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Optional

from jam.block import Block
from jam.log_setup import block_logger as logger
from rockstore import RockStore
from jam.types.protocol.crypto import Hash
from jam.telemetry import emit_event
from jam.telemetry.events import FinalizedBlockChanged
from tsrkit_types import U32, Bytes32

if TYPE_CHECKING:
    from jam.block.block_view import BlockView, Heads, GhostBlock
    from jam.jam_node import JamNode


class FinalityService:
    """
    Instant finality service.
    To be replaced by GRANDPA.

    Keeps track of finalised and latest header hashes, using which we can fetch its corresponding blocks
    """

    FINAL_KEY = bytes(Hash.blake2b(b"FINAL_BLOCK"))
    LATEST_KEY = bytes(Hash.blake2b(b"LATEST_BLOCK"))
    HEADS_KEY = bytes(Hash.blake2b(b"LATEST_HEADS"))
    META_KEY = bytes(Hash.blake2b(b"BLOCK_META"))

    def __init__(self, jam: "JamNode"):
        self.jam = jam
        self.block_view = jam.ledger
        self.db = jam.settings.main_db

    @property
    def settings(self):
        return self.jam.settings

    def finalise(self, block: Block, initial: bool = True, sch_ts: int = 18):
        """Finalizes block and updates Block View.

        Note: For delayed finalization (initial=False), this now schedules
        the finalization asynchronously to avoid blocking the event loop.
        """
        header_hash = block.header.hash()

        if initial:
            logger.info(f"Finalized {header_hash.encode().hex()[0:16]}...")
            self.db.put(self.FINAL_KEY, header_hash.encode())
            self._complete_finalization(block, header_hash)
        else:
            # Schedule delayed finalization without blocking
            asyncio.create_task(self._delayed_finalise(block, header_hash, sch_ts))

    async def _delayed_finalise(self, block: Block, header_hash, sch_ts: int):
        """Async delayed finalization - does not block the event loop."""
        await asyncio.sleep(sch_ts)  # Non-blocking sleep
        logger.info(f"Finalized {header_hash.encode().hex()[0:16]}...")
        self.db.put(self.FINAL_KEY, header_hash.encode())
        self._complete_finalization(block, header_hash)

    def _complete_finalization(self, block: Block, header_hash):
        """Complete the finalization process (shared logic)."""
        emit_event(
            FinalizedBlockChanged(slot=U32(block.header.slot), hash=Bytes32(header_hash.encode()))
        )

        # Timeslot -> HeaderHash
        # on finalization of block, store ts - block mapping
        ts_key = block.get_storage_key_slot(block.header.slot)
        self.db.put(ts_key, header_hash)

        self.block_view.finalize(block)

    def set_head(self, block: Block):
        """Records new blocks and update heads of chains."""

        self.db.put(self.LATEST_KEY, block.header.hash().encode())

        self.block_view.record_block(block)
        self.db.put(self.HEADS_KEY, self.block_view.heads.encode())

        # self.block_view.visualize()

    def load_final(self) -> Block:
        """Load latest finalized block."""

        final_hh = self.db.get(self.FINAL_KEY)
        if not final_hh:
            return Block.genesis()
        return Block.load(final_hh, self.db)

    def load_latest(self) -> Block:
        """Load last intercepted block."""

        latest_hh = self.db.get(self.LATEST_KEY)
        if not latest_hh:
            latest_hh = bytes(32)
        return Block.load(latest_hh, self.db)

    def load_heads(self) -> Heads | Block:
        """Load all the heads available."""

        data = self.db.get(self.HEADS_KEY)

        if data:
            heads = Heads.decode(data)
            return heads

        else:
            block = self.load_final()
            return block

    def load_best(self) -> Block:
        """Loads best block."""

        best = self.block_view.best

        return Block.load(best.header, self.db)


    def load_best_head(self) -> Block:
        """Loads best block."""

        best = self.block_view.best

        if best is None:
            raise ValueError("BlockView.best is None")

        heads_set = set(self.block_view.heads)
        current = best
        best_match: Optional[GhostBlock] = None

        while True:
            # If this block is a head, record it
            if current.header in heads_set:
                best_match = current

            # No children → stop
            if not current.children:
                break

            # By invariant: 0 or 1 child only
            current = current.children[0]

        block = best_match if best_match is not None else best

        return Block.load(block.header, self.db)
