import asyncio
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
    async def schedule_run(cls, header_hash: HeaderHash, kv: RockStore, sch_ts: int, initial: bool ) -> None:
        if initial:
            logger.info(f"Finalized {header_hash.encode().hex()[0:16]}...")
            kv.put(cls.FINAL_KEY, header_hash.encode())
        else:
            await asyncio.sleep(sch_ts)
            logger.info(f"Finalized {header_hash.encode().hex()[0:16]}...")
            kv.put(cls.FINAL_KEY, header_hash.encode())

        # publish updates of the latest finalized block
        asyncio.create_task(subscribe_finalized_block(header_hash))

    @classmethod
    def finalise(cls, header_hash: HeaderHash, kv: RockStore, initial: bool):
        asyncio.create_task(cls.schedule_run(header_hash, kv, 18, initial))

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
    def load_latest(cls, kv: RockStore) -> "Block":
        latest_hh = kv.get(cls.LATEST_KEY)
        if not latest_hh:
            latest_hh = bytes(32)
        return Block.load(latest_hh, kv)
