from dataclasses import dataclass
from jam.types.base.choices.option import Option, decodable_option
from jam.types.base.null import Null
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base import Vector, decodable_vector
from jam.types.extrinsics.tickets import TicketBody
from jam.types.protocol.core import TimeSlot, ValidatorIndex
from jam.types.protocol.epoch import EpochMark
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import (
    BandersnatchVrfSignature,
    Ed25519Public,
    HeaderHash,
    StateRoot,
    OpaqueHash,
)
from jam.utils.constants import EPOCH_LENGTH
from jam.utils.json.serde import JsonSerde
from tests.fixtures.utils import create_dummy_bytes, create_dummy_bytes32, create_dummy_int

"""Fixed-length array of ticket bodies."""


@decodable_array(length=EPOCH_LENGTH, element_type=TicketBody)
class TicketsMark(Array[TicketBody]):
    ...


@decodable_vector(element_type=Ed25519Public)
class OffendersMark(Vector[Ed25519Public]):
    ...


@decodable_option(EpochMark)
class OptionalEpochMark(Option):
    ...


@decodable_option(TicketsMark)
class OptionalTicketsMark(Option):
    ...


@decodable_dataclass
@dataclass
class Header(Codable, JsonSerde):
    """Block header structure."""

    parent: HeaderHash
    parent_state_root: StateRoot
    extrinsic_hash: OpaqueHash
    slot: TimeSlot
    epoch_mark: OptionalEpochMark
    tickets_mark: OptionalTicketsMark
    offenders_mark: OffendersMark
    author_index: ValidatorIndex
    entropy_source: BandersnatchVrfSignature
    seal: BandersnatchVrfSignature

    @staticmethod
    def from_random(seed: int = 0) -> "Header":
        """
        Create a random header
        """
        return Header(
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
        )

    def load_parent(slot: TimeSlot) -> "Header":
        """
        Get the parent header hash
        """
        return Header.from_random(int(slot - 1))

    def load(slot: TimeSlot) -> "Header":
        """
        Load the header for the given slot from DB
        TODO: Implement
        """
        return Header.from_random(int(slot - 1))

    async def save(self):
        """
        Save the header to DB
        TODO: Implement
        """
        ...