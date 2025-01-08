from dataclasses import dataclass
from typing import List, Any, Tuple, Sequence
from enum import Enum

from jam.types.base.sequences.array import Array
from jam.types.base.boolean import Boolean
from jam.types.base.integers.fixed import U16, U32
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import (
    Ed25519Public, Ed25519Signature,
    OpaqueHash, WorkReportHash
)
from jam.types.protocol.core import ValidatorIndex
from jam.utils.codec.composite.arrays import ArrayCodec
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY

@dataclass
class Judgement(Codable):
    """Judgement structure."""
    vote: Boolean
    index: ValidatorIndex
    signature: Ed25519Signature

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.vote, self.index, self.signature]

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
        vote, size = Boolean.decode_from(buffer, current_offset)
        current_offset += size
        index, size = ValidatorIndex.decode_from(buffer, current_offset)
        current_offset += size
        signature, size = Ed25519Signature.decode_from(buffer, current_offset)
        current_offset += size
        return Judgement(vote, index, signature), current_offset - offset

@dataclass
class Culprit(Codable):
    """Culprit structure."""
    target: WorkReportHash
    key: Ed25519Public
    signature: Ed25519Signature

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.target, self.key, self.signature]

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
        target, size = WorkReportHash.decode_from(buffer, current_offset)
        current_offset += size
        key, size = Ed25519Public.decode_from(buffer, current_offset)
        current_offset += size
        signature, size = Ed25519Signature.decode_from(buffer, current_offset)
        current_offset += size
        return Culprit(target, key, signature), current_offset - offset

@dataclass
class Fault(Codable):
    """Fault structure."""
    target: WorkReportHash
    vote: Boolean
    key: Ed25519Public
    signature: Ed25519Signature

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.target, self.vote, self.key, self.signature]

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
        target, size = WorkReportHash.decode_from(buffer, current_offset)
        current_offset += size
        vote, size = Boolean.decode_from(buffer, current_offset)
        current_offset += size
        key, size = Ed25519Public.decode_from(buffer, current_offset)
        current_offset += size
        signature, size = Ed25519Signature.decode_from(buffer, current_offset)
        current_offset += size
        return Fault(target, vote, key, signature), current_offset - offset

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Fault):
            return self.target == value.target and self.vote == value.vote and self.key == value.key and self.signature == value.signature
        return False

class JudgementVotes(Array[Judgement]):
    """Judgement votes array."""
    def __init__(self, values: List[Judgement]):
        super().__init__(VALIDATORS_SUPER_MAJORITY, values)

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        judgements, size = ArrayCodec.decode_from(VALIDATORS_SUPER_MAJORITY, Judgement, buffer, offset)
        return JudgementVotes(judgements), size

@dataclass
class Verdict(Codable):
    """Verdict structure."""
    target: WorkReportHash
    age: U32
    votes: JudgementVotes

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.target, self.age, self.votes]

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
        target, size = WorkReportHash.decode_from(buffer, offset)
        current_offset = offset + size
        age, size = U32.decode_from(buffer, current_offset)
        current_offset += size
        votes, size = JudgementVotes.decode_from(buffer, current_offset)
        current_offset += size
        return Verdict(target, age, votes), current_offset - offset

@decodable_vector(WorkReportHash)
class WorkReportHashes(Vector[WorkReportHash]): pass

@decodable_vector(Ed25519Public)
class Offenders(Vector[Ed25519Public]): pass

@dataclass
class DisputesRecords(Codable):
    """Disputes records structure."""
    good: WorkReportHashes
    bad: WorkReportHashes
    wonky: WorkReportHashes
    offenders: Offenders

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.good, self.bad, self.wonky, self.offenders]

    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())
    
    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        good, size = WorkReportHashes.decode_from(buffer, offset)
        current_offset = offset + size
        bad, size = WorkReportHashes.decode_from(buffer, current_offset)
        current_offset += size
        wonky, size = WorkReportHashes.decode_from(buffer, current_offset)
        current_offset += size
        offenders, size = Offenders.decode_from(buffer, current_offset)
        current_offset += size
        return DisputesRecords(good, bad, wonky, offenders), current_offset - offset


@decodable_vector(Verdict)
class Verdicts(Vector[Verdict]): pass;

@decodable_vector(Culprit)
class Culprits(Vector[Culprit]): pass;

@decodable_vector(Fault)
class Faults(Vector[Fault]): pass;

@dataclass
class DisputesExtrinsic(Codable):
    """Disputes extrinsic structure."""
    verdicts: Verdicts
    culprits: Culprits
    faults: Faults

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.verdicts, self.culprits, self.faults]

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
        verdicts, size = Verdicts.decode_from(buffer, offset)
        current_offset = offset + size
        culprits, size = Culprits.decode_from(buffer, current_offset)
        current_offset += size
        faults, size = Faults.decode_from(buffer, current_offset)
        current_offset += size
        return DisputesExtrinsic(Vector(verdicts), Vector(culprits), Vector(faults)), current_offset - offset
