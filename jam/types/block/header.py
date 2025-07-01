import json
from tsrkit_types.option import Option
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from jam.types import (
    BandersnatchVrfSignature,
    Ed25519Public,
    Hash,
    HeaderHash,
    StateRoot,
    OpaqueHash,
    EpochMark,
    TimeSlot, ValidatorIndex,
    TicketsMark
)


OffendersMark = TypedVector[Ed25519Public]


@structure
class Header:
    """Block header structure."""

    parent: HeaderHash
    parent_state_root: StateRoot
    extrinsic_hash: OpaqueHash
    slot: TimeSlot
    epoch_mark: Option[EpochMark]
    tickets_mark: Option[TicketsMark]
    offenders_mark: OffendersMark
    author_index: ValidatorIndex
    entropy_source: BandersnatchVrfSignature
    seal: BandersnatchVrfSignature

    def __hash__(self) -> int:
        return int.from_bytes(self.hash())

    def __str__(self):
        return (
            f"Header(\n"
            f"  parent={self.parent.hex()},\n"
            f"  state_root={self.parent_state_root.hex()},\n"
            f"  extrinsic_hash={self.extrinsic_hash.hex()},\n"
            f"  slot={self.slot},\n"
            f"  epoch_mark={self.epoch_mark},\n"
            f"  tickets_mark={self.tickets_mark},\n"
            f"  offenders_mark={self.offenders_mark},\n"
            f"  author_index={self.author_index},\n"
            f"  entropy_source={self.entropy_source.hex()},\n"
            f"  seal={self.seal.hex()}\n"
            f")"
        )

    def hash(self) -> bytes:
        return Hash.blake2b(self.encode())
    
    @staticmethod
    def genesis(path = "genesis.json") -> "Header":
        return Header.from_json(json.load(open(path))["header"])