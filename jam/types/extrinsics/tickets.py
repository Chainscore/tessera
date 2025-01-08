from dataclasses import dataclass
from typing import List, Any, Tuple, Optional, Sequence
from enum import Enum

from jam.types.base.integers.fixed import U16, U32, U8
from jam.types.base.sequences.array import Array
from jam.types.base.bytes import Bytes
from jam.types.base import Vector
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import (
    BandersnatchPublic, BandersnatchVrfSignature,
    BandersnatchRingVrfSignature, HeaderHash,
    StateRoot, OpaqueHash
)
from jam.utils.codec.composite.arrays import ArrayCodec
from jam.utils.codec.composite.vectors import VectorCodec
from jam.utils.constants import (
    EPOCH_LENGTH,
    MAX_TICKETS_PER_EXTRINSIC
)

TicketId = OpaqueHash
TicketAttempt = U8

@dataclass
class TicketEnvelope(Codable):
    """Ticket entry structure."""
    attempt: TicketAttempt
    signature: BandersnatchRingVrfSignature

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.attempt, self.signature]

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
        attempt, size = TicketAttempt.decode_from(buffer, current_offset)
        current_offset += size
        signature, size = BandersnatchRingVrfSignature.decode_from(buffer, current_offset)
        current_offset += size
        return TicketEnvelope(attempt, signature), current_offset - offset

@dataclass
class TicketBody(Codable):
    """Ticket body structure."""
    id: TicketId
    attempt: TicketAttempt

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.id, self.attempt]

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
        id, size = TicketId.decode_from(buffer, current_offset)
        current_offset += size
        attempt, size = TicketAttempt.decode_from(buffer, current_offset)
        current_offset += size
        return TicketBody(id, attempt), current_offset - offset

class TicketsAccumulator(Array[TicketBody]):
    """Fixed-size array of ticket bodies for an extrinsic."""
    def __init__(self, entries: List[TicketBody]):
        super().__init__(EPOCH_LENGTH, entries)
    
    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        entries = []
        for _ in range(EPOCH_LENGTH):
            ticket, size = TicketBody.decode_from(buffer, offset)
            entries.append(ticket)
            offset += size
        return TicketsAccumulator(entries), offset

class KeysAccumulator(Array[BandersnatchPublic]):
    """Fixed-size array of public keys for an extrinsic."""
    def __init__(self, entries: List[BandersnatchPublic]):
        super().__init__(EPOCH_LENGTH, entries)
    
    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        values, size = ArrayCodec.decode_from(EPOCH_LENGTH, BandersnatchPublic, buffer, offset)
        return KeysAccumulator(values), size 

class TicketsExtrinsic(Vector[TicketEnvelope]):
    """Fixed-size array of ticket envelopes for an extrinsic."""
    def __init__(self, entries: List[TicketEnvelope]):
        super().__init__(entries)
    
    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        values, size = VectorCodec.decode_from(TicketEnvelope, buffer, offset)
        return TicketsExtrinsic(values), size 
