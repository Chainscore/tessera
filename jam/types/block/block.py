from tsrkit_types.struct import structure

from rockstore import RockStore

from jam.logging import get_logger
from jam.types import TimeSlot
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
    def from_random(seed: int = 0, n_et=3, n_ep=3, n_ea=3, n_eg=3, n_ed=2) -> "Block":
        """
        Create a random block
        """
        return Block(
            header=create_dummy_header(),
            extrinsic=create_dummy_extrinsics(n_et, n_ep, n_ea, n_eg, n_ed),
        )

    @staticmethod
    def genesis(path="dev-spec.json") -> "Block":
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

        data = db.get(cls.get_storage_key_block(header_hash))
        if data is None:
            raise ValueError("No block found header hash: ", header_hash.hex())
        return cls.decode(data)

    @classmethod
    def load_w_ts(cls, ts: TimeSlot, db: RockStore) -> "Block":
        ts_key = cls.get_storage_key_slot(ts)
        header_hash = db.get(ts_key)
        return cls.load(header_hash, db)

    @staticmethod
    def get_storage_key_block(header_hash: HeaderHash) -> bytes:
        return Hash.blake2b("HH_TO_BLOCK".encode() + header_hash)

    @staticmethod
    def get_storage_key_slot(slot: TimeSlot) -> bytes:
        return Hash.blake2b("TIMESLOT_TO_HH".encode() + slot.encode())

    def save(self, db: RockStore) -> HeaderHash:
        """
        Save the block to DB
        """
        block_encoded = self.encode()
        hh = self.header.hash()
        logger.debug(
            "💾 Saving block",
            header_hash=hh.hex(),
            slot=self.header.slot,
            len=len(block_encoded),
        )

        # HeaderHash -> Block
        hh_key = self.get_storage_key_block(self.header.hash())
        db.put(hh_key, block_encoded)
        # Timeslot -> HeaderHash
        ts_key = self.get_storage_key_slot(self.header.slot)
        db.put(ts_key, hh)

        # Return the HeaderHash
        return HeaderHash(hh)
