from dataclasses import dataclass, field

from rockstore import RockStore

from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types import structure
from tsrkit_types.dictionary import Dictionary

from jam.types.work.report import WorkReportHash
from tsrkit_types.integers import Uint

SignatureList=TypedVector[Bytes]

@structure
class JudgmentRecord:
    true_votes: SignatureList #J_t(wr)(t)
    false_votes: SignatureList # J_f(wr)(t)
    announces: SignatureList #A_n

    @staticmethod
    def dummy()-> "JudgmentRecord":
        true_votes:SignatureList=SignatureList([Bytes(0),Bytes(1)])
        false_votes:SignatureList=SignatureList([])
        announces:SignatureList=SignatureList([Bytes(0),Bytes(1),Bytes(2),Bytes(3),Bytes(4),Bytes(5)])
        return JudgmentRecord(true_votes=true_votes,false_votes=false_votes,announces=announces)

    @staticmethod
    def empty()->"JudgmentRecord":
        return JudgmentRecord(true_votes=SignatureList([]),false_votes=SignatureList([]),announces=SignatureList([]))

@structure
class TrancheState:
    unaudited_list: TypedVector[WorkReportHash] #Q ->[wr1,2,3,4]->[]
    judgments: Dictionary[WorkReportHash, JudgmentRecord] # {WR:J,S}
    valid_set: TypedVector[WorkReportHash] # Already validated_wrs [wr,1,2,3,4]
    invalid_set: TypedVector[WorkReportHash] # Already invalid_wrs

    @staticmethod
    def empty()->"TrancheState":
        return TrancheState(
            unaudited_list=TypedVector[WorkReportHash]([]),
            judgments=Dictionary[WorkReportHash, JudgmentRecord]({}),
            valid_set=TypedVector[WorkReportHash]([]),
            invalid_set=TypedVector[WorkReportHash]([])
        )

    # def add_wr(self, wrs: WorkReportHash):
    #     for wr in wrs
    #         if wr not in self.judgments:
    #             self.judgments[wr] = JudgmentRecord()
    #         if wr not in self.unaudited_list:
    #             self.unaudited_list.append(wr)

    # def add_valid_wr(self,wrs:TypedVector[WorkReportHash]):
    #     self.valid_set.extend(wrs)
    #     self.unaudited_list.remove(wrs)

    # def record_announcement(self, wr: WorkReportHash, judgment: Bytes):
    #     self.add_wr(wr)
    #     self.judgments[wr].announces.append(judgment)

    # def record_judgment(self, wr: WorkReportHash, judgment: Bytes, is_true: bool):
    #     self.add_wr(wr)
    #     if is_true:
    #         self.judgments[wr].true_votes.append(judgment)
    #     else:
    #         self.judgments[wr].false_votes.append(judgment)

@structure
# @dataclass
class Tranche:
    tranche_index: Uint
    slot_index: Uint

    def db_key(self) -> Bytes:
        """
        Returns a consistent DB key: Tranche.encode()
        """
        return self.encode()

    def save_state(self, db: RockStore, tranche_state: TrancheState):
        """
        Stores the TrancheState encoded under Tranche.encode() key.
        """
        db.put(self.db_key(), tranche_state.encode())

    def load_state(self, db: RockStore) :
        """
        Loads the TrancheState encoded under Tranche.encode() key.
        """
        raw = db.get(self.db_key())
        if raw:
            return TrancheState.decode(raw)
        else:
            return TrancheState.empty()  # Return empty state if not found
