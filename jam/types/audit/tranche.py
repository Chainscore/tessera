from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.integers import U8
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.struct import structure
from tsrkit_types.option import Option

from jam.types.protocol.crypto import HeaderHash
from jam.types.protocol.core import ValidatorIndex
from jam.types.work.report import WorkReport, WorkReportHash

SignatureList=TypedVector[Bytes]
ValidatorList=TypedVector[ValidatorIndex]

TrancheIndex = U8
OptionalReport = Option[WorkReport]

@structure
class JudgmentRecord:
    true_votes: ValidatorList #J_t(wr)(t)
    false_votes: ValidatorList # J_f(wr)(t)
    announces: ValidatorList #A_n

    @staticmethod
    def dummy()-> "JudgmentRecord":
        true_votes:ValidatorList=ValidatorList([])
        false_votes:ValidatorList=ValidatorList([ValidatorIndex(0)])
        announces:ValidatorList=ValidatorList([ValidatorIndex(0),ValidatorIndex(1),ValidatorIndex(2),ValidatorIndex(3),ValidatorIndex(4),ValidatorIndex(5)])
        return JudgmentRecord(true_votes=true_votes,false_votes=false_votes,announces=announces)

    @staticmethod
    def empty()->"JudgmentRecord":
        return JudgmentRecord(true_votes=ValidatorList([]),false_votes=ValidatorList([]),announces=ValidatorList([]))

@structure
class TrancheState:
    unaudited_list: TypedVector[OptionalReport] #Q ->[wr1,2,3,4]->[]
    judgments: Dictionary[WorkReportHash, JudgmentRecord] # {WR:J,S}
    valid_set: TypedVector[WorkReportHash] # Already validated_wrs [wr,1,2,3,4]
    invalid_set: TypedVector[WorkReportHash] # Already invalid_wrs

    @staticmethod
    def empty()->"TrancheState":
        return TrancheState(
            unaudited_list=TypedVector[OptionalReport]([]),
            judgments=Dictionary[WorkReportHash, JudgmentRecord]({}),
            valid_set=TypedVector[WorkReportHash]([]),
            invalid_set=TypedVector[WorkReportHash]([])
        )

@structure
class Tranche:
    tranche_index: TrancheIndex
    header_hash: HeaderHash

    def __hash__(self):
        return hash((self.tranche_index, self.header_hash))
