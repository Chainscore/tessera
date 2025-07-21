from dataclasses import dataclass, field

from rockstore import RockStore

from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types import structure
from tsrkit_types.dictionary import Dictionary

from jam.types.protocol.core import ValidatorIndex
from jam.types.work.report import WorkReport, WorkReportHash
from tsrkit_types.integers import Uint

SignatureList=TypedVector[Bytes]
ValidatorList=TypedVector[ValidatorIndex]
EncodedWR=bytes

@structure
class JudgmentRecord:
    true_votes: ValidatorList #J_t(wr)(t)
    false_votes: ValidatorList # J_f(wr)(t)
    announces: ValidatorList #A_n

    @staticmethod
    def dummy()-> "JudgmentRecord":
        true_votes:ValidatorList=ValidatorList([])
        false_votes:ValidatorList=ValidatorList([ValidatorIndex(0),ValidatorIndex(1),ValidatorIndex(2),ValidatorIndex(3)])
        announces:ValidatorList=ValidatorList([ValidatorIndex(0),ValidatorIndex(1),ValidatorIndex(2),ValidatorIndex(3),ValidatorIndex(4),ValidatorIndex(5)])
        return JudgmentRecord(true_votes=true_votes,false_votes=false_votes,announces=announces)

    @staticmethod
    def empty()->"JudgmentRecord":
        return JudgmentRecord(true_votes=ValidatorList([]),false_votes=ValidatorList([]),announces=ValidatorList([]))

@structure
class TrancheState:
    unaudited_list: TypedVector[WorkReport] #Q ->[wr1,2,3,4]->[]
    judgments: Dictionary[EncodedWR, JudgmentRecord] # {WR:J,S}
    valid_set: TypedVector[WorkReport] # Already validated_wrs [wr,1,2,3,4]
    invalid_set: TypedVector[WorkReport] # Already invalid_wrs

    @staticmethod
    def empty()->"TrancheState":
        return TrancheState(
            unaudited_list=TypedVector[WorkReport]([]),
            judgments=Dictionary[EncodedWR, JudgmentRecord]({}),
            valid_set=TypedVector[WorkReport]([]),
            invalid_set=TypedVector[WorkReport]([])
        )

@structure
# @dataclass
class Tranche:
    tranche_index: Uint[32]
    slot_index: Uint[32]

class TrancheStore:
    def __init__(self):
        self._tranche_store={}

    def save(self, tranche: "Tranche", state: "TrancheState"):
        """Store TrancheState under its tranche key automatically."""
        key = tranche.encode()
        value = state.encode()
        self._tranche_store[key]= value

    def load(self, tranche: "Tranche") -> "TrancheState":
        """Retrieve and decode a TrancheState by Tranche object."""
        raw = self._tranche_store.get(tranche.encode())
        return TrancheState.decode(raw) if raw else TrancheState.empty()

    def delete(self, tranche: "Tranche"):
        key = tranche.encode()
        if key in self._tranche_store:
            del self._tranche_store[key]
