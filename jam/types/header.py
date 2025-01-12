from dataclasses import dataclass
from typing import Optional
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base import Vector, decodable_vector
from jam.types.extrinsics.tickets import TicketBody
from jam.types.protocol.core import TimeSlot, ValidatorIndex
from jam.types.protocol.epoch import EpochMark
from jam.utils.codec import Codable, decodable_dataclass
from jam.types.protocol.crypto import (
    BandersnatchVrfSignature, Ed25519Public, HeaderHash, StateRoot, OpaqueHash,
)
from jam.utils.constants import EPOCH_LENGTH

"""Fixed-length array of ticket bodies."""
@decodable_array(length=EPOCH_LENGTH, element_type=TicketBody)
class TicketsMark(Array[TicketBody]): ...

@decodable_vector(element_type=Ed25519Public)
class OffendersMark(Vector[Ed25519Public]): ...

@decodable_dataclass
@dataclass
class Header(Codable):
    """Block header structure."""
    parent: HeaderHash
    parent_state_root: StateRoot
    extrinsic_hash: OpaqueHash
    slot: TimeSlot
    epoch_mark: Optional[EpochMark]
    tickets_mark: Optional[TicketsMark]
    offenders_mark: OffendersMark
    author_index: ValidatorIndex
    entropy_source: BandersnatchVrfSignature
    seal: BandersnatchVrfSignature
