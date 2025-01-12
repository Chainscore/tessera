from dataclasses import dataclass
from jam.types.base.boolean import Boolean
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.codec import Codable, decodable_dataclass
from jam.types.protocol.crypto import (
    Ed25519Public, Ed25519Signature,
    WorkReportHash
)
from jam.types.protocol.core import ValidatorIndex
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY

@decodable_dataclass
@dataclass
class Judgement(Codable):
    """Judgement structure."""
    vote: Boolean
    index: ValidatorIndex
    signature: Ed25519Signature

@decodable_dataclass
@dataclass
class Culprit(Codable):
    """Culprit structure."""
    target: WorkReportHash
    key: Ed25519Public
    signature: Ed25519Signature

@decodable_dataclass
@dataclass
class Fault(Codable):
    """Fault structure."""
    target: WorkReportHash
    vote: Boolean
    key: Ed25519Public
    signature: Ed25519Signature

@decodable_array(length=VALIDATORS_SUPER_MAJORITY, element_type=Judgement)
class JudgementVotes(Array[Judgement]): ...

@decodable_dataclass
@dataclass
class Verdict(Codable):
    """Verdict structure."""
    target: WorkReportHash
    age: U32
    votes: JudgementVotes

@decodable_vector(WorkReportHash)
class WorkReportHashes(Vector[WorkReportHash]): ...

@decodable_vector(Ed25519Public)
class Offenders(Vector[Ed25519Public]): ...

@decodable_dataclass
@dataclass
class DisputesRecords(Codable):
    """Disputes records structure."""
    good: WorkReportHashes
    bad: WorkReportHashes
    wonky: WorkReportHashes
    offenders: Offenders

@decodable_vector(Verdict)
class Verdicts(Vector[Verdict]): ...

@decodable_vector(Culprit)
class Culprits(Vector[Culprit]): ...

@decodable_vector(Fault)
class Faults(Vector[Fault]): ...

@decodable_dataclass
@dataclass
class DisputesExtrinsic(Codable):
    """Disputes extrinsic structure."""
    verdicts: Verdicts
    culprits: Culprits
    faults: Faults