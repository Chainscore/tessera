from jam.block.extrinsics.store import ExtrinsicStore
from tsrkit_types.bool import Bool
from tsrkit_types.integers import U32
from tsrkit_types.sequences import TypedArray, TypedVector
from tsrkit_types.struct import structure

from jam.models.protocol.crypto import Ed25519Public, Ed25519Signature, WorkReportHash
from jam.models.protocol.core import ValidatorIndex
from jam.utils.constants import VALIDATOR_COUNT


@structure
class Judgement:
    """Judgement structure."""

    vote: Bool
    index: ValidatorIndex
    signature: Ed25519Signature


@structure
class Culprit:
    """Culprit structure."""

    target: WorkReportHash
    key: Ed25519Public
    signature: Ed25519Signature


@structure
class Fault:
    """Fault structure."""

    target: WorkReportHash
    vote: Bool
    key: Ed25519Public
    signature: Ed25519Signature


JudgementVotes = TypedVector[Judgement]


@structure
class Verdict:
    """Verdict structure."""

    target: WorkReportHash
    age: U32
    votes: JudgementVotes


WorkReportHashes = TypedVector[WorkReportHash]

Offenders = TypedVector[Ed25519Public]


@structure
class DisputesRecords:
    """Disputes records structure."""

    good: WorkReportHashes
    bad: WorkReportHashes
    wonky: WorkReportHashes
    offenders: Offenders


Verdicts = TypedVector[Verdict]

Culprits = TypedVector[Culprit]

Faults = TypedVector[Fault]


@structure
class DisputesExtrinsic:
    """Disputes extrinsic structure."""

    verdicts: Verdicts
    culprits: Culprits
    faults: Faults

    @classmethod
    def empty(cls):
        return cls(verdicts=Verdicts([]), culprits=Culprits([]), faults=Faults([]))

dpt_store = ExtrinsicStore[DisputesExtrinsic]()
