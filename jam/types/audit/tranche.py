from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.integers import U8
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.struct import structure
from tsrkit_types.option import Option

from jam.network.protocols.ce_144 import Announcement
from jam.types.protocol.crypto import HeaderHash, Hash
from jam.types.protocol.core import ValidatorIndex
from jam.types.work.report import WorkReport, WorkReportHash, WorkReports

SignatureList=TypedVector[Bytes]
ValidatorList=TypedVector[ValidatorIndex]

TrancheIndex = U8
OptionalReport = Option[WorkReport]


@structure
class AuditRecord:
    true_votes: ValidatorList #J_t(wr)(t)  Carry Forward
    false_votes: ValidatorList # J_f(wr)(t) Carry Forward
    announces: ValidatorList #A_n
    no_votes: ValidatorList

    @staticmethod
    def empty() -> "AuditRecord":
        return AuditRecord(announces=ValidatorList([]), true_votes=ValidatorList([]), false_votes=ValidatorList([]),
                           no_votes=ValidatorList([]))

@structure
class TrancheState:
    unaudited_list: TypedVector[OptionalReport] # Corpus of reports (q), a_n will be calculated from this.
    announcements: Dictionary[ValidatorIndex, Announcement] # Announcements received in this tranche
    assigned_wrs: WorkReports
    records: Dictionary[WorkReportHash, AuditRecord] # A_n, J_t, J_f mappings.

    valid_set: TypedVector[WorkReportHash] # Already validated_wrs [wr,1,2,3,4]
    invalid_set: TypedVector[WorkReportHash] # Already invalid_wrs

    @staticmethod
    def empty()->"TrancheState":
        return TrancheState(
            unaudited_list=TypedVector[OptionalReport]([]),
            announcements=Dictionary[ValidatorIndex, Announcement]({}),
            assigned_wrs=WorkReports([]),

            records=Dictionary[WorkReportHash, AuditRecord]({}),

            valid_set=TypedVector[WorkReportHash]([]),
            invalid_set=TypedVector[WorkReportHash]([])
        )

@structure
class Tranche:
    tranche_index: TrancheIndex
    header_hash: HeaderHash

    def __hash__(self):
        return Hash.blake2b(self.encode())