import json
from tsrkit_types.option import Option
from tsrkit_types.sequences import TypedArray, TypedVector
from tsrkit_types.struct import structure
from jam.types.extrinsics.tickets import TicketBody
from jam.types.protocol.core import TimeSlot, ValidatorIndex
from jam.types.protocol.epoch import EpochMark
from jam.types.protocol.crypto import (
    BandersnatchVrfSignature,
    Ed25519Public,
    Hash,
    HeaderHash,
    StateRoot,
    OpaqueHash,
)
from jam.utils.constants import EPOCH_LENGTH

"""Fixed-length array of ticket bodies."""
TicketsMark = TypedArray[TicketBody, EPOCH_LENGTH]

OffendersMark = TypedVector[Ed25519Public]

OptionalEpochMark = Option[EpochMark]

OptionalTicketsMark = Option[TicketsMark]


@structure
class Header:
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
        return int(Hash.blake2b(self.encode()))
    
    @staticmethod
    def genesis(path = "genesis.json") -> "Header":
        return Header.from_json(json.load(open(path))["header"])