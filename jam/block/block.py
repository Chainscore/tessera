from typing import Self, List

from jam.models.protocol.ticket import TicketBody
from tsrkit_types.struct import structure
from rockstore import RockStore
from jam.log_setup import block_logger as logger
from jam.models import TimeSlot
from jam.block.extrinsics.extrinsic import Extrinsic
from jam.block.header import Header
from jam.models.protocol.crypto import Hash, HeaderHash

from jam.utils.dummy.dummy_extrinsics import create_dummy_extrinsics
from jam.utils.dummy.dummy_header import create_dummy_header


@structure
class Block:
    """Block structure."""

    header: Header
    extrinsic: Extrinsic

    def __str__(self):
        return (f"Block(hh={self.header.hash().hex()}, "
                f"parent={self.header.parent.hex()}, "
                f"slot={self.header.slot}, "
                f"author={self.header.author_index})")

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
        try:
            return Block(header=Header.genesis(path), extrinsic=Extrinsic.empty())
        except TypeError:
            from jam.block.header import EpochMark, OffendersMark, TicketsMark
            from jam.models import (
                BandersnatchVrfSignature,
                OpaqueHash,
                StateRoot,
                TimeSlot,
                ValidatorIndex,
            )
            from tsrkit_types import Null

            return Block(
                header=Header(
                    parent=HeaderHash(32),
                    parent_state_root=StateRoot(32),
                    extrinsic_hash=OpaqueHash(32),
                    slot=TimeSlot(0),
                    epoch_mark=EpochMark(Null),
                    tickets_mark=TicketsMark(Null),
                    author_index=ValidatorIndex(0),
                    entropy_source=BandersnatchVrfSignature(96),
                    offenders_mark=OffendersMark([]),
                    seal=BandersnatchVrfSignature(96),
                ),
                extrinsic=Extrinsic.empty(),
            )

    def load_parent(self, db: RockStore) -> "Block":
        """
        Get the parent block
        """
        return Block.load(self.header.parent, db)

    @classmethod
    def load(cls, header_hash: HeaderHash, db: RockStore) -> Self | None:
        """
        Load the block for the given slot from DB
        """
        if header_hash == bytes(32):
            # Return genesis block
            return Block.genesis()

        data = db.get(cls.get_storage_key_block(header_hash))
        if data is None:
            return None
        return cls.decode(data)

    @classmethod
    def load_header(cls, header_hash: HeaderHash, db: RockStore) -> Header | None:
        if header_hash == bytes(32):
            return Header.genesis()

        data = db.get(cls.get_storage_key_block(header_hash))
        if data is None:
            return None

        header, _ = Header.decode_from(data)
        return header

    @classmethod
    def load_parent_hash(cls, header_hash: HeaderHash, db: RockStore) -> HeaderHash | None:
        if header_hash == bytes(32):
            return HeaderHash(32)

        data = db.get(cls.get_storage_key_block(header_hash))
        if data is None:
            return None

        return HeaderHash(data[:32])

    @classmethod
    def load_w_ts(cls, ts: TimeSlot, db: RockStore) -> "Block" | List["Block"]:

        from jam.block.block_view import viewer
        final = viewer.final

        ts_key = cls.get_storage_key_slot(ts)

        # if ts is before or equal to that than directly load from db
        if ts <= final.slot:
            header_hash = db.get(ts_key)
            if not header_hash:
                raise ValueError("No block found with given slot!")
            return cls.load(header_hash, db)

        # otherwise load using block viewer
        else:
            blocks = viewer.load_block_w_ts(ts, db)
            if len(blocks) == 0:
                raise ValueError("No block found with given slot!")

            logger.debug("Loaded blocks.", slot=ts, cnt=len(blocks))
            return blocks

    @staticmethod
    def get_storage_key_block(header_hash: HeaderHash) -> bytes:
        return Hash.blake2b("HH_TO_BLOCK".encode() + header_hash)

    @staticmethod
    def get_storage_key_slot(slot: TimeSlot) -> bytes:
        val = "TIMESLOT_TO_HH".encode() + slot.encode()
        val += bytes(32 - len(val))
        return val

    @staticmethod
    def get_storage_key_meta(header_hash: HeaderHash) -> bytes:
        return b"BLOCK_META" + header_hash

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
        hh_key = self.get_storage_key_block(hh)
        db.put(hh_key, block_encoded)

        # Return the HeaderHash
        return hh

    def validate(self, state, prestate, settings) -> bool:
        return self.header.validate(state, prestate, settings) and self.extrinsic.validate(self.header)

    def produce(self, time_slot: TimeSlot, state, settings, ticket: TicketBody | None = None) -> "Block":
        extrinsic = Extrinsic.from_collected(time_slot)

        # Produce a new header from previous header
        header = self.header.produce(time_slot, extrinsic, ticket, state, settings)

        block = Block(header=header, extrinsic=extrinsic)

        return block
