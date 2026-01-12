from typing import TYPE_CHECKING
from rockstore import RockStore
from jam.types.protocol.crypto import Hash
from jam.block import Block
from jam.block.block_view import Heads
from tsrkit_types import Bytes32

if TYPE_CHECKING:
    from jam.block.block_view import Heads

class Finality:
    """
    Compatibility shim for static Finality access.
    Deprecated: Use FinalityService where possible.
    """
    FINAL_KEY = bytes(Hash.blake2b(b"FINAL_BLOCK"))
    LATEST_KEY = bytes(Hash.blake2b(b"LATEST_BLOCK"))
    HEADS_KEY = bytes(Hash.blake2b(b"LATEST_HEADS"))
    META_KEY = bytes(Hash.blake2b(b"BLOCK_META"))

    @staticmethod
    def load_final(kv: RockStore) -> Block:
        """Load latest finalized block."""
        final_hh = kv.get(Finality.FINAL_KEY)
        if not final_hh:
            return Block.genesis()
        return Block.load(final_hh, kv)

    @staticmethod
    def load_latest(kv: RockStore) -> Block:
        """Load last intercepted block."""
        latest_hh = kv.get(Finality.LATEST_KEY)
        if not latest_hh:
            latest_hh = bytes(32)
        return Block.load(latest_hh, kv)

    @staticmethod
    def load_heads(kv: RockStore) -> Heads | Block:
        """Load all the heads available."""
        data = kv.get(Finality.HEADS_KEY)
        if data:
            heads = Heads.decode(data)
            return heads
        else:
            block = Finality.load_final(kv)
            return block
