import asyncio
import time
from jam.log_setup import block_logger as logger
from rockstore import RockStore
from jam.types.protocol.crypto import Hash, HeaderHash
from jam.block import Block
from jam.api.rpc.subscription_handlers import subscribe_finalized_block, subscribe_best_block

class Finality:
    """
    Instant finality
    To be replaced by GRANDPA

    Keeps track of finalised and latest header hashes, using which we can fetch its corresponding blocks
    """

    FINAL_KEY = bytes(Hash.blake2b(b"FINAL_BLOCK"))
    LATEST_KEY = bytes(Hash.blake2b(b"LATEST_BLOCK"))

    @classmethod
    def finalise(cls, header_hash: HeaderHash, kv: RockStore, initial: bool = True, sch_ts: int = 18):
        if initial:
            logger.info(f"Finalized {header_hash.encode().hex()[0:16]}...")
            kv.put(cls.FINAL_KEY, header_hash.encode())
        else:
            time.sleep(sch_ts)
            logger.info(f"Finalized {header_hash.encode().hex()[0:16]}...")
            kv.put(cls.FINAL_KEY, header_hash.encode())

        # publish updates of the latest finalized block
        asyncio.create_task(subscribe_finalized_block(header_hash))

    @classmethod
    def set_head(cls, header_hash: HeaderHash, kv: RockStore):
        kv.put(cls.LATEST_KEY, header_hash.encode())
        # publish updates of the head of the "best" chain.
        asyncio.create_task(subscribe_best_block(header_hash))

    @classmethod
    def load_final(cls, kv: RockStore) -> "Block":
        final_hh = kv.get(cls.FINAL_KEY)
        if not final_hh:
            final_hh = bytes(32)
        return Block.load(final_hh, kv)

    @classmethod
    def load_latest(cls, kv: RockStore):
        latest_hh = kv.get(cls.LATEST_KEY)
        if not latest_hh:
            latest_hh = bytes(32)
        return Block.load(latest_hh, kv)

    @classmethod
    def best_block(cls, block: Block):
        """
        Checking condition for best block.
        1. Has finalized block as an ancestor.
        2. Single validator can't produce two diff block in same timeslot.
        3. Is considered audited.

        Args:
            block: Block for checking best block

        """
        from jam.settings import settings as _set

        is_audited = False
        is_finalized_ancestor = False
        is_audited = False

        latest_finalized_block = cls.load_final(kv=_set.main_db)

        if latest_finalized_block.header.hash() == block.header.hash():
            logger.error("latest finalized block and current process block can't have same header hash")
            raise

        parent_hash = block.header.parent

        # -------------------- 1. Parent ancestor checked --------------------
        while not is_finalized_ancestor:
            parent_block = Block.load(header_hash=parent_hash, db=_set.main_db)
            if parent_block.header.hash() == latest_finalized_block:
                is_finalized_ancestor = True
                break

            # keep moving to parent block
            parent_hash = parent_block.header.parent

        # 3. -------------------- Block audited --------------------
        from jam.audit.audit_engine import AuditEngine
        engine = AuditEngine()
        audited = engine.get_audit_status()
        if audited:
            is_audited =True
        else:
            logger.warning(
                f"Block with header_hash {block.header.hash()} not audited"
            )

        # 3. -------------------- FORK => 1V , 2 diff B , in same slot --------------------
        ...
