from dataclasses import dataclass
import json
from jam.types.base.choices.option import Option, decodable_option
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
    Hash,
    HeaderHash,
    StateRoot,
    OpaqueHash,
)
from jam.utils.constants import EPOCH_LENGTH
from jam.utils.json.serde import JsonSerde
from jam.types.base.sequences.bytes.byte_array import ByteArray32

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

    def __hash__(self) -> int:
        return int.from_bytes(bytes(Hash.blake2b(self.encode())))
    
    @staticmethod
    def genesis(path = "genesis.json") -> "Header":
        return Header.from_json(json.load(open(path))["header"])