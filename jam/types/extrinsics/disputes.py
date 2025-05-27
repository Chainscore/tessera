from dataclasses import dataclass
from jam.storage.db.kv import KVStore
from jam.storage.queue import StorageQueue
from jam.types.base.boolean import Boolean
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import Ed25519Public, Ed25519Signature, WorkReportHash
from jam.types.protocol.core import ValidatorIndex
from jam.utils.constants import VALIDATOR_COUNT
from jam.utils.json.serde import JsonSerde


@decodable_dataclass
@dataclass
class Judgement(Codable, JsonSerde):
    """Judgement structure."""

    vote: Boolean
    index: ValidatorIndex
    signature: Ed25519Signature


@decodable_dataclass
@dataclass
class Culprit(Codable, JsonSerde):
    """Culprit structure."""

    target: WorkReportHash
    key: Ed25519Public
    signature: Ed25519Signature


@decodable_dataclass
@dataclass
class Fault(Codable, JsonSerde):
    """Fault structure."""

    target: WorkReportHash
    vote: Boolean
    key: Ed25519Public
    signature: Ed25519Signature


@decodable_array(length=(1 + VALIDATOR_COUNT * 2 // 3), element_type=Judgement)
class JudgementVotes(Array[Judgement]):
    ...


@decodable_dataclass
@dataclass
class Verdict(Codable, JsonSerde):
    """Verdict structure."""

    target: WorkReportHash
    age: U32
    votes: JudgementVotes


@decodable_vector(WorkReportHash)
class WorkReportHashes(Vector[WorkReportHash]):
    ...


@decodable_vector(Ed25519Public)
class Offenders(Vector[Ed25519Public]):
    ...


@decodable_dataclass
@dataclass
class DisputesRecords(Codable, JsonSerde):
    """Disputes records structure."""

    good: WorkReportHashes
    bad: WorkReportHashes
    wonky: WorkReportHashes
    offenders: Offenders


@decodable_vector(Verdict)
class Verdicts(Vector[Verdict]):
    ...


@decodable_vector(Culprit)
class Culprits(Vector[Culprit]):
    ...


@decodable_vector(Fault)
class Faults(Vector[Fault]):
    ...


@decodable_dataclass
@dataclass
class DisputesExtrinsic(Codable, JsonSerde):
    """Disputes extrinsic structure."""

    verdicts: Verdicts
    culprits: Culprits
    faults: Faults