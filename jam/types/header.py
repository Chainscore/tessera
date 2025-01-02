from dataclasses import dataclass
from typing import Any, List, Sequence, Tuple, Union

from jam.types.base.array import Array
from jam.types.base.bytes import Bytes
from jam.types.base.choice import Choice
from jam.types.base.integers import U16
from jam.types.base.null import Null
from jam.types.base.option import Option
from jam.types.base.vector import Vector
from jam.types.extrinsics.tickets import TicketBody
from jam.types.protocol.core import ErasureRoot, ExportsRoot, TimeSlot, ValidatorIndex
from jam.types.protocol.validators import ValidatorArray
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import (
    BandersnatchPublic, BandersnatchVrfSignature, Ed25519Public,
    HeaderHash, StateRoot, OpaqueHash, Entropy,
    BeefyRoot
)
from jam.utils.codec.composite.arrays import ArrayCodec
from jam.utils.codec.composite.vectors import VectorCodec
from jam.utils.constants import EPOCH_LENGTH, VALIDATOR_COUNT


@dataclass
class EpochMark(Codable):
    entropy: Entropy
    tickets_entropy: Entropy
    validators: ValidatorArray

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.entropy, self.tickets_entropy, self.validators]
    
    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())
    
    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset
    
    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        entropy, size = Entropy.decode_from(buffer, current_offset)
        current_offset += size
        tickets_entropy, size = Entropy.decode_from(buffer, current_offset)
        current_offset += size
        validators, size = ValidatorArray.decode_from(buffer, current_offset)
        current_offset += size
        return EpochMark(entropy, tickets_entropy, validators), current_offset - offset


class TicketsMark(Array[TicketBody]):
    def __init__(self, entries: List[TicketBody]):
        super().__init__(EPOCH_LENGTH, entries)

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        return ArrayCodec.decode_from(EPOCH_LENGTH, TicketBody, buffer, offset)


class OffendersMark(Vector[Ed25519Public]):
    def __init__(self, entries: List[Ed25519Public]):
        super().__init__(entries)
    
    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        return VectorCodec.decode_from(Ed25519Public, buffer, offset)


@dataclass
class Header(Codable):
    """Block header structure."""
    parent: HeaderHash
    parent_state_root: StateRoot
    extrinsic_hash: OpaqueHash
    slot: TimeSlot
    epoch_mark: Option
    tickets_mark: Option
    offenders_mark: OffendersMark
    author_index: ValidatorIndex
    entropy_source: BandersnatchVrfSignature
    seal: BandersnatchVrfSignature

    def enc_sequence(self) -> Sequence[Codable]:
        sequence = [
            self.parent, self.parent_state_root, self.extrinsic_hash,
            self.slot, self.epoch_mark, self.tickets_mark, self.offenders_mark,
            self.author_index, self.entropy_source, self.seal
        ]
        return sequence

    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        parent, size = HeaderHash.decode_from(buffer, current_offset)
        current_offset += size
        state_root, size = StateRoot.decode_from(buffer, current_offset)
        current_offset += size
        extrinsic_hash, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        slot, size = TimeSlot.decode_from(buffer, current_offset)
        current_offset += size
        epoch_mark, size = Option.decode_from(EpochMark, buffer, current_offset)
        current_offset += size
        tickets_mark, size = Option.decode_from(TicketsMark, buffer, current_offset)
        current_offset += size
        offenders_mark, size = OffendersMark.decode_from(buffer, current_offset)
        current_offset += size
        author_index, size = ValidatorIndex.decode_from(buffer, current_offset)
        current_offset += size
        entropy_source, size = BandersnatchVrfSignature.decode_from(buffer, current_offset)
        current_offset += size
        seal, size = BandersnatchVrfSignature.decode_from(buffer, current_offset)
        current_offset += size
        return Header(parent, state_root, extrinsic_hash, slot, epoch_mark,
                     tickets_mark, offenders_mark, author_index,
                     entropy_source, seal), current_offset - offset