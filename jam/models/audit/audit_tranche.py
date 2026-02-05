from dataclasses import dataclass
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.struct import structure
from tsrkit_types.option import Option
from jam.network.protocols.ce_144 import NoShows
from jam.models.protocol.crypto import HeaderHash, Hash, Ed25519Signature, Ed25519Public
from jam.models.protocol.core import ValidatorIndex, TrancheIndex, CoreIndex, EpochIndex
from jam.models.work.report import WorkReport, WorkReportHash

SignatureList = TypedVector[Bytes]
ValidatorSet = set[ValidatorIndex]

OptionalReport = Option[WorkReport]
OptionalReports = TypedVector[OptionalReport]


@dataclass(frozen=True)
class JudgmentData:
    """Validator judgment with their ed25519_public key and signature structure."""

    epoch_index: EpochIndex
    validator_index: ValidatorIndex
    ed25519_public: Ed25519Public
    ed25519_signature: Ed25519Signature


JudgmentSet = set[JudgmentData]


@structure
class CoreReport:
    """Work Report associated with their Core Index."""

    core_index: CoreIndex
    work_report: WorkReport


@structure
class CoreOptionalReport:
    """Optional Work Report associated with their Core Index."""

    core_index: CoreIndex
    work_report: OptionalReport


@structure
class AuditRecord:
    """Managing auditing records based on tranche."""

    announces: ValidatorSet
    true_votes: JudgmentSet
    false_votes: JudgmentSet
    no_shows: NoShows

    @staticmethod
    def empty() -> "AuditRecord":
        """Initialized empty audit records"""
        return AuditRecord(
            announces=ValidatorSet(), true_votes=JudgmentSet(), false_votes=JudgmentSet(), no_shows=NoShows([])
        )

    def carry_forward(self) -> "AuditRecord":
        """Forward work reports judgment records for next Tranche (for same slot)"""
        return AuditRecord(
            announces=ValidatorSet(),
            true_votes=self.true_votes,
            false_votes=self.false_votes,
            no_shows=NoShows([]),
        )


class Records(Dictionary[WorkReportHash, AuditRecord]):
    """Clear Announcement and No_Show for new Tranche (for same slot)"""

    def clear_an(self) -> "Records":
        new_records: Records = Records({wrh: rec.carry_forward() for wrh, rec in self.items()})

        return new_records


@structure
class TrancheState:
    """Represents the tranche state, which maintains audit records associated with each tranche."""

    unaudited_list: OptionalReports
    records: Records
    audited_list: TypedVector[CoreReport]

    @staticmethod
    def empty() -> "TrancheState":
        """Creates and returns an initialized empty state object."""
        return TrancheState(
            unaudited_list=OptionalReports([]),
            records=Records({}),
            audited_list=TypedVector[CoreReport]([]),
        )

    def carry_forward(self) -> "TrancheState":
        """Carry forward and returns an initialized empty state object."""
        return TrancheState(
            unaudited_list=OptionalReports([]),
            records=self.records.clear_an(),
            audited_list=self.audited_list,
        )


@structure
class Tranche:
    """Represents a Tranche containing a header hash and a tranche index."""

    tranche_index: TrancheIndex
    header_hash: HeaderHash

    def __repr__(self) -> str:
        short_hash = self.header_hash.hex()[:16]
        idx = int(self.tranche_index)
        return f"Tranche({short_hash}@{idx})"

    def __hash__(self) -> int:
        return int.from_bytes(Hash.blake2b(self.encode()), byteorder="big")
