from tsrkit_types import Bytes
from tsrkit_types.struct import structure

from rockstore import RockStore

from jam.config.logging import get_logger
from jam.types.block.extrinsics.extrinsic import Extrinsic
from jam.types.block.header import Header
from jam.types.protocol.crypto import Hash, HeaderHash
from jam.utils.dummy.dummy_extrinsics import create_dummy_extrinsics
from jam.utils.dummy.dummy_header import create_dummy_header

logger = get_logger("author")

@structure
class Block:
    """Block structure."""

    header: Header
    extrinsic: Extrinsic

    @staticmethod
    def from_random(seed: int = 0, n_et = 3, n_ep = 3, n_ea = 3, n_eg = 3, n_ed = 3) -> "Block":
        """
        Create a random block
        """
        return Block(header=create_dummy_header(), extrinsic=create_dummy_extrinsics(n_et, n_ep, n_ea, n_eg, n_ed))
    
    @staticmethod
    def genesis(path = "genesis.json") -> "Block":
        return Block(header=Header.genesis(path), extrinsic=Extrinsic.empty())

    def load_parent(self, db: RockStore) -> "Block":
        """
        Get the parent block
        """
        return Block.load(self.header.parent, db)

    @classmethod
    def load(cls, header_hash: HeaderHash, db: RockStore) -> "Block":
        """
        Load the block for the given slot from DB
        """
        if bytes(header_hash) == bytes(32):
            # Return genesis block
            raise ValueError("Reached end of the chain")
        
        data = db.get(header_hash)
        if data is None:
            raise ValueError("No block found header hash: ", header_hash.hex())
        return cls.decode(data)
        
    def save(self, db: RockStore) -> HeaderHash:
        """
        Save the block to DB
        """
        data = self.encode()
        header_hash = self.header.hash()
        logger.debug("💾 Saving block", header_hash=header_hash.hex(), len=len(data))
        # HeaderHash -> Block
        db.put(header_hash, data)
        # Timeslot -> HeaderHash
        db.put(self.header.slot.encode(), header_hash)

        # Return the HeaderHash
        return HeaderHash(header_hash)
