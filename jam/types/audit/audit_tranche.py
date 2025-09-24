from dataclasses import dataclass
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.struct import structure
from tsrkit_types.option import Option
from jam.network.protocols.ce_144 import NoShows, CoreReportHash
from jam.types.protocol.crypto import HeaderHash, Hash, Ed25519Signature, Ed25519Public
from jam.types.protocol.core import ValidatorIndex, TrancheIndex, CoreIndex, EpochIndex
from jam.types.work.report import WorkReport, WorkReportHash

SignatureList = TypedVector[Bytes]
ValidatorSet = set[ValidatorIndex]

OptionalReport = Option[WorkReport]
OptionalReports = TypedVector[OptionalReport]


@dataclass(frozen=True)
class JudgmentData:
    """ Validator judgment with their ed25519_public key and signature structure. """

    epoch_index: EpochIndex
    validator_index: ValidatorIndex
    ed25519_public: Ed25519Public
    ed25519_signature: Ed25519Signature

judgmentSet = set[JudgmentData]

@structure
class CoreReport:
    """ Work Report associated with their Core Index. """
    core_index: CoreIndex
    work_report: WorkReport

@structure
class CoreOptionalReport:
    """Optional Work Report associated with their Core Index. """
    core_index: CoreIndex
    work_report: OptionalReport

@structure
class AuditRecord:
    """ Managing auditing records based on tranche. """
    announces: ValidatorSet
    true_votes: judgmentSet
    false_votes: judgmentSet
    no_shows: NoShows


    @staticmethod
    def empty() -> "AuditRecord":
        """ Initialized empty audit records """
        return AuditRecord(
            announces= ValidatorSet(),
            true_votes= set(),
            false_votes= set(),
            no_shows= NoShows([])
        )

    def carry_forward(self) -> "AuditRecord":
        """ Forward work reports judgment records for next Tranche (for same slot) """
        return AuditRecord(
            announces= ValidatorSet(),
            true_votes= self.true_votes,
            false_votes= self.false_votes,
            no_shows= NoShows([])
        )

class Records(Dictionary[WorkReportHash, AuditRecord]):
    """ Clear Announcement and No_Show for new Tranche (for same slot) """

    def clear_an(self) -> "Records":
        new_records = Records({
            wrh: rec.carry_forward() for wrh, rec in self.items()
        })

        return new_records

@structure
class TrancheState:
    """ Represents the tranche state, which maintains audit records associated with each tranche. """
    unaudited_list: OptionalReports
    records: Records
    audited_list: TypedVector[CoreReportHash]


    @staticmethod
    def empty() -> "TrancheState":
        """ Creates and returns an initialized empty state object. """
        return TrancheState(
            unaudited_list= OptionalReports([]),
            records= Records({}),
            audited_list= TypedVector[CoreReportHash]([]),
       )

    def carry_forward(self) -> "TrancheState":
        """ Carry forward and returns an initialized empty state object. """
        return TrancheState(
            unaudited_list= OptionalReports([]),
            records= self.records.clear_an(),
            audited_list= self.audited_list,
        )

@structure
class Tranche:
    """Represents a Tranche containing a header hash and a tranche index."""
    tranche_index: TrancheIndex
    header_hash: HeaderHash

    def __repr__(self):
        return f"Tranche: {self.header_hash.hex()[:16]}@{int(self.tranche_index)}"

    def __hash__(self):
        return int.from_bytes(Hash.blake2b(self.encode()))


