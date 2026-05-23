import asyncio
import time

from jam.block.block_view import Heads
from jam.log_setup import block_logger as logger
from rockstore import RockStore
from jam.models.protocol.crypto import Hash, HeaderHash
from jam.block import Block
from jam.api.rpc.subscription_handlers import subscribe_finalized_block
from jam.telemetry import emit_event
from jam.telemetry.events import FinalizedBlockChanged
from tsrkit_types import U32, Bytes32




class Finality:
    """
    Instant finality
    To be replaced by GRANDPA

    Keeps track of finalised and latest header hashes, using which we can fetch its corresponding blocks
    """

    FINAL_KEY = bytes(Hash.blake2b(b"FINAL_BLOCK"))
    LATEST_KEY = bytes(Hash.blake2b(b"LATEST_BLOCK"))
    HEADS_KEY = bytes(Hash.blake2b(b"LATEST_HEADS"))
    META_KEY = bytes(Hash.blake2b(b"BLOCK_META"))

    FINALITY_CONFIRMATION_DEPTH = 2

    @classmethod
    def finalise(cls, block: Block, kv: RockStore, initial: bool = True, sch_ts: int = 18):
        """Finalizes block and updates Block View."""

        header_hash = block.header.hash()

        logger.info(f"Finalized {header_hash.encode().hex()[0:16]}...")
        kv.put(cls.FINAL_KEY, header_hash.encode())

        emit_event(FinalizedBlockChanged(slot=U32(block.header.slot), hash=Bytes32(header_hash.encode())))
        
        # publish updates of the latest finalized block
        asyncio.create_task(subscribe_finalized_block(header_hash))

        # Timeslot -> HeaderHash
        # on finalization of block, store ts - block mapping
        ts_key = block.get_storage_key_slot(block.header.slot)
        kv.put(ts_key, header_hash)
        from jam.block.block_view import viewer
        viewer.finalize(block, kv)

    @classmethod
    def advance_finalized(cls, head_block: Block, kv: RockStore, depth: int = None):
        """Finalize the ancestor `depth` blocks behind `head_block`, settling its
        state into the base store and pruning losing forks. Advance-forward-only."""
        import jam.state.state as state_mod
        from jam.block.block_view import viewer

        if depth is None:
            depth = cls.FINALITY_CONFIRMATION_DEPTH

        target = head_block
        for _ in range(depth):
            parent_hh = target.header.parent
            if parent_hh == HeaderHash(32):
                return
            parent_block = Block.load(parent_hh, kv)
            if parent_block is None:
                return
            target = parent_block

        f_hh = target.header.hash()

        current_final = cls.load_final(kv)
        if current_final is None:
            return
        if f_hh == current_final.header.hash():
            return
        if int(target.header.slot) <= int(current_final.header.slot):
            return

        if viewer.load_ghost(f_hh) is None:
            return

        base = state_mod.state.store
        updates, _final_root = base.load_cache(f_hh, apply_trie=True)
        for k, v in updates.items():
            try:
                if v is None:
                    base._DB.delete(k)
                else:
                    base._DB.put(k, v)
            except Exception:
                pass

        cls.finalise(target, kv, initial=True)

    @classmethod
    def set_head(cls, block: Block, kv: RockStore):
        """Records new blocks and update heads of chains."""

        kv.put(cls.LATEST_KEY, block.header.hash().encode())

        from jam.block.block_view import viewer
        viewer.record_block(block, kv)
        kv.put(cls.HEADS_KEY, viewer.heads.encode())

        # viewer.visualize()

    @classmethod
    def load_final(cls, kv: RockStore) -> Block:
        """Load latest finalized block."""

        final_hh = kv.get(cls.FINAL_KEY)
        if not final_hh:
            return Block.genesis()
        return Block.load(final_hh, kv)

    @classmethod
    def load_latest(cls, kv: RockStore) -> Block:
        """Load last intercepted block."""

        latest_hh = kv.get(cls.LATEST_KEY)
        if not latest_hh:
            latest_hh = bytes(32)
        return Block.load(latest_hh, kv)

    @classmethod
    def load_heads(cls, kv: RockStore) -> Heads | Block:
        """Load all the heads available."""

        data = kv.get(cls.HEADS_KEY)

        if data:
            heads = Heads.decode(data)
            return heads

        else:
            block = cls.load_final(kv)
            return block

    @classmethod
    def load_best(cls, kv: RockStore) -> Block:
        """Loads best block."""

        from jam.block.block_view import viewer
        best = viewer.best

        return Block.load(best.header, kv)
