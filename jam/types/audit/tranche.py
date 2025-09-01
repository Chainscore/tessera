from typing import TYPE_CHECKING, Tuple
from tsrkit_types import Null
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.integers import U8
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.struct import structure
from tsrkit_types.option import Option

from jam.block.extrinsics.disputes import DisputesExtrinsic, Verdicts, Culprits, Faults
from jam.network.protocols.ce_144 import NoShows
from jam.types.protocol.crypto import HeaderHash, Hash, Ed25519Signature, Ed25519Public
from jam.types.protocol.core import ValidatorIndex, TrancheIndex, CoreIndex
from jam.types.work.report import WorkReport, WorkReportHash

SignatureList = TypedVector[Bytes]
ValidatorList = TypedVector[ValidatorIndex]

OptionalReport = Option[WorkReport]
OptionalReports = TypedVector[OptionalReport]

@structure
class ValidatorSignature:
    """Validator signature structure."""

    validator_index: ValidatorIndex
    ed25519_public: Ed25519Public
    signature: Ed25519Signature

judgments = TypedVector[ValidatorSignature]

@structure
class CoreReport:
    core_index: CoreIndex
    report_hash: WorkReportHash

@structure
class AuditRecord:
    announces: ValidatorList            # A_n
    true_votes: judgments               # J_t(wr)(t, key and sign) => Carry Forward
    false_votes: judgments              # J_f(wr)(t, key and sign) => Carry Forward
    no_shows: NoShows


    @staticmethod
    def empty() -> "AuditRecord":
        """ Initialized empty audit records """
        return AuditRecord(
            announces= ValidatorList([]),
            true_votes= judgments([]),
            false_votes= judgments([]),
            no_shows= NoShows([])
        )

    def carry_forward(self) -> "AuditRecord":
        """ Forward work reports judgment records for next Tranche (for same slot) """
        return AuditRecord(
            announces= ValidatorList([]),
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
    unaudited_list: OptionalReports                                             # Corpus of reports (q), a_n will be calculated from this.
    records: Records                                                            # A_n, J_t, J_f mappings.
    valid_set: TypedVector[CoreReport]                                          # Already validated_wrs [(1, wr1), (4, wr4), ....]
    invalid_set: TypedVector[CoreReport]                                        # Already invalid_wrs [(2, wr1), (5, wr4), ....]
    dispute: DisputesExtrinsic


    @staticmethod
    def empty() -> "TrancheState":
        """ Creates and returns an initialized empty state object. """
        return TrancheState(
            unaudited_list=OptionalReports([]),
            records=Records({}),
            valid_set=TypedVector[WorkReportHash]([]),
            invalid_set=TypedVector[WorkReportHash]([]),
            dispute=DisputesExtrinsic(
                verdicts=Verdicts([]),
                culprits=Culprits([]),
                faults=Faults([])
            )
       )

    def carry_forward(self) -> "TrancheState":
        """ Carry forward and returns an initialized empty state object. """
        return TrancheState(
            unaudited_list=OptionalReports([]),
            records=self.records.clear_an(),
            valid_set=self.valid_set,
            invalid_set=self.invalid_set,
            dispute=DisputesExtrinsic(
                verdicts=Verdicts([]),
                culprits= Culprits([]),
                faults= Faults([])
            )
        )

@structure
class Tranche:
    tranche_index: TrancheIndex
    header_hash: HeaderHash

    def __repr__(self):
        return f"Tranche: {self.header_hash.hex()[:16]}@{int(self.tranche_index)}"

    def __hash__(self):
        return int.from_bytes(Hash.blake2b(self.encode()))