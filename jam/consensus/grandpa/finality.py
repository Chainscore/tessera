import asyncio
from jam.logging import get_logger
from rockstore import RockStore
from jam.api.rpc.websocket import ws_broker

from jam.types.block import Block
from jam.types.protocol.crypto import Hash, HeaderHash

logger = get_logger("grandpa")

class Finality:
    """
    Instant finality
    To be replaced by GRANDPA

    Keeps track of finalised and latest header hashes, using which we can fetch its corresponding blocks
    """

    FINAL_KEY = bytes(Hash.blake2b(b"FINAL_BLOCK"))
    LATEST_KEY = bytes(Hash.blake2b(b"LATEST_BLOCK"))

    @classmethod
    def finalise(cls, header_hash: HeaderHash, kv: RockStore):
        # asyncio.create_task(ws_broker.publish("final", {"" : header_hash}))
        logger.debug("Finalised block", header_hash=header_hash.hex())
        kv.put(cls.FINAL_KEY, header_hash.encode())

    @classmethod
    def set_head(cls, header_hash: HeaderHash, kv: RockStore):
        logger.debug("Setting header...", header_hash=header_hash.hex())
        kv.put(cls.LATEST_KEY, header_hash.encode())

    @classmethod
    def load_final(cls, kv: RockStore) -> Block:
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
