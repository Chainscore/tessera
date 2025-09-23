import asyncio
from jam.log_setup import block_logger as logger
from rockstore import RockStore
from jam.types.protocol.crypto import Hash, HeaderHash
from jam.block import Block
from jam.api.rpc.broker import broker

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
        from jam.settings import settings
        if initial:
            logger.info(f"Finalized {header_hash.encode().hex()[0:16]}...")
            kv.put(cls.FINAL_KEY, header_hash.encode())
            block = Block.load(header_hash, kv)
            if settings.rpc_flag:
                # Subscribe's to updates of the latest finalized block, as returned by finalizedBlock.
                asyncio.create_task(broker.publish("subscribeFinalizedBlock",
                                                   {"header_hash": list(header_hash), "slot": int(block.header.slot)}))
        else:
            await asyncio.sleep(sch_ts)
            logger.info(f"Finalized {header_hash.encode().hex()[0:16]}...")
            kv.put(cls.FINAL_KEY, header_hash.encode())
            block = Block.load(header_hash, kv)
            if settings.rpc_flag:
                # Subscribe's to updates of the latest finalized block, as returned by finalizedBlock.
                asyncio.create_task(broker.publish("subscribeFinalizedBlock",
                                                   {"header_hash": list(header_hash), "slot": int(block.header.slot)}))

    @classmethod
    def finalise(cls, header_hash: HeaderHash, kv: RockStore, initial: bool):
        # asyncio.create_task(ws_broker.publish("final", {"" : header_hash}))
        logger.debug("Finalised block", header_hash=header_hash.hex())
        asyncio.create_task(cls.schedule_run(header_hash, kv, 18, initial))

    @classmethod
    def set_head(cls, header_hash: HeaderHash, kv: RockStore):
        from jam.settings import settings
        # logger.debug("Setting header...", header_hash=header_hash.hex())
        if settings.rpc_flag:
            block = Block.load(header_hash, kv)
            #Subscribe's to updates of the head of the "best" chain, as returned by bestBlock.
            if block:
                asyncio.create_task(broker.publish("subscribeBestBlock", {"header_hash":list(header_hash), "slot":int(block.header.slot)}))
            else:
                logger.warning("Head published, but not found in store", header_hash=header_hash.hex())
        kv.put(cls.LATEST_KEY, header_hash.encode())

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
