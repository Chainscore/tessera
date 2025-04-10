from dataclasses import dataclass

from jam.db.kv import KVStore
from jam.types.base.null import Null
from jam.types.extrinsics.disputes import Culprits, Faults, Verdicts
from jam.types.header import Header, OffendersMark, OptionalEpochMark, OptionalTicketsMark
from jam.utils.codec.codable import Codable
from jam.types.extrinsics import (
    TicketsExtrinsic,
    PreimagesExtrinsic,
    GuaranteesExtrinsic,
    AssurancesExtrinsic,
    DisputesExtrinsic,
)
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.serde import JsonSerde
from jam.types.protocol.crypto import (
    BandersnatchVrfSignature,
    Hash,
    HeaderHash,
    StateRoot,
    OpaqueHash,
)
from tests.fixtures.utils import create_dummy_bytes, create_dummy_bytes32, create_dummy_int
from jam.types.protocol.core import TimeSlot, ValidatorIndex


@decodable_dataclass
@dataclass
class Extrinsic(Codable, JsonSerde):
    """Extrinsic structure."""

    tickets: TicketsExtrinsic
    preimages: PreimagesExtrinsic
    guarantees: GuaranteesExtrinsic
    assurances: AssurancesExtrinsic
    disputes: DisputesExtrinsic


@decodable_dataclass
@dataclass
class Block(Codable, JsonSerde):
    """Block structure."""

    header: Header
    extrinsic: Extrinsic

    @staticmethod
    def from_random(seed: int = 0) -> "Block":
        """
        Create a random block
        """
        return Block(header=Header(
            parent=HeaderHash(create_dummy_bytes32(seed)),
            parent_state_root=StateRoot(create_dummy_bytes32(seed)),
            extrinsic_hash=OpaqueHash(create_dummy_bytes32(seed)),
            slot=TimeSlot(create_dummy_int(16, seed)),
            epoch_mark=OptionalEpochMark(Null),
            tickets_mark=OptionalTicketsMark(Null),
            offenders_mark=OffendersMark([]),
            entropy_source=BandersnatchVrfSignature(create_dummy_bytes(96, seed)),
            author_index=ValidatorIndex(create_dummy_int(8, seed)),
            seal=BandersnatchVrfSignature(create_dummy_bytes(96, seed)),
        ), extrinsic=Extrinsic(
            tickets=TicketsExtrinsic([]),
            preimages=PreimagesExtrinsic([]),
            guarantees=GuaranteesExtrinsic([]),
            assurances=AssurancesExtrinsic([]),
            disputes=DisputesExtrinsic(
                culprits=Culprits([]),
                faults=Faults([]),
                verdicts=Verdicts([])
            )
        ))

    def load_parent(slot: TimeSlot, db: KVStore) -> "Block":
        """
        Get the parent block
        """
        # Keep going 1 slot back until we find a block
        while True:
            slot -= 1
            if slot < 0:
                raise ValueError("No parent block found")
            data = db.get(Block.storage_key(slot))
            if data is not None:
                block, _ = Block.decode_from(data)
                return block

    def load(slot: TimeSlot, db: KVStore) -> "Block":
        """
        Load the block for the given slot from DB
        """
        data = db.get(Block.storage_key(slot))
        if data is None:
            raise ValueError("No block found for slot: ", slot)
        block, _ = Block.decode_from(data)
        return block
        
    def save(self, db: KVStore):
        """
        Save the block to DB
        """
        db.put(Block.storage_key(self.header.slot), self.encode())

    @staticmethod
    def storage_key(slot: TimeSlot) -> bytes:
        """
        Get the storage key for the block
        """
        return bytes(Hash.blake2b("Block_".encode() + slot.encode()))
