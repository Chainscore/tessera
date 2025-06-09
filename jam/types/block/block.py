from tsrkit_types.struct import structure

from rockstore import RockStore
from jam.types.block.extrinsics.extrinsic import Extrinsic
from jam.types.block.header import Header
from jam.types.protocol.crypto import Hash
from jam.utils.dummy.dummy_extrinsics import create_dummy_extrinsics
from jam.utils.dummy.dummy_header import create_dummy_header
from jam.types.protocol.core import TimeSlot


@structure
class Block:
    """Block structure."""

    header: Header
    extrinsic: Extrinsic

    @staticmethod
    def from_random(seed: int = 0, n_et = 3, n_ep = 3, n_ea = 3, n_eg = 3, n_ed = 2) -> "Block":
        """
        Create a random block
        """
        return Block(header=create_dummy_header(), extrinsic=create_dummy_extrinsics(n_et, n_ep, n_ea, n_eg, n_ed))
    
    @staticmethod
    def genesis(path = "genesis.json") -> "Block":
        return Block(header=Header.genesis(path), extrinsic=Extrinsic.empty())

    @staticmethod
    def load_parent(slot: TimeSlot, db: RockStore) -> "Block":
        """
        Get the parent block
        """
        while True:
            slot -= 1
            if slot < 0:
                raise ValueError("Parent does of exist of genesis block")
            try:
                return Block.load(slot, db)
            except ValueError:
                continue

    @classmethod
    def load(cls, slot: TimeSlot, db: RockStore) -> "Block":
        """
        Load the block for the given slot from DB
        """
        if slot == 0:
            # Return genesis block
            return Block.genesis()
        
        data = db.get(Block.storage_key(slot))
        if data is None:
            raise ValueError("No block found for slot: ", slot)
        return cls.decode(data)
        
    def save(self, db: RockStore):
        """
        Save the block to DB
        """
        db.put(Block.storage_key(self.header.slot), self.encode())
        # Achieve finality immediately
        db.put(bytes(Hash.blake2b(b"finality")), self.header.slot.encode())

    @staticmethod
    def storage_key(slot: TimeSlot) -> bytes:
        """
        Get the storage key for the block
        """
        return bytes(Hash.blake2b("Block_".encode() + slot.encode()))
