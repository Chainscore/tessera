from typing import Dict
from structlog import get_logger

from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types import U8, structure
from tsrkit_types.dictionary import Dictionary

from jam.types.protocol.core import TrancheIndex, ValidatorIndex
from jam.types.protocol.crypto import HeaderHash, Hash
from jam.types.work.report import WorkReport, WorkReportHash


logger = get_logger("tranch_storing")

SignatureList=TypedVector[Bytes]
ValidatorList=TypedVector[ValidatorIndex]
EncodedWR=Bytes # Later might be replaced with Work Report Itself.

@structure
class JudgmentRecord:
    true_votes: ValidatorList #J_t(wr)(t)
    false_votes: ValidatorList # J_f(wr)(t)
    announces: ValidatorList #A_n

    @staticmethod
    def dummy()-> "JudgmentRecord":
        false_votes:ValidatorList=ValidatorList([])
        true_votes:ValidatorList=ValidatorList([ValidatorIndex(0),ValidatorIndex(1),ValidatorIndex(2),ValidatorIndex(3)])
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
    tranche_index: TrancheIndex
    header_hash: HeaderHash

    def __hash__(self):
        return hash((self.tranche_index, self.header_hash))


class TrancheStore:
    """Persistent store for Tranches"""
    _tranche_store: Dict[Tranche, TrancheState]

    def __init__(self) -> None:
        self._tranche_store = {}

    def _get_state(self, tranche: Tranche) -> TrancheState:
        """Retrieve a TrancheState by Tranche object."""
        state = self._tranche_store.get(tranche)
        return state if state is not None else TrancheState.empty()

    def _save_state(self, tranche: Tranche, state: TrancheState):
        """Store TrancheState under its tranche key automatically."""
        self._tranche_store[tranche] = state

    def delete_tranche(self, tranche: Tranche):
        if tranche in self._tranche_store:
            del self._tranche_store[tranche]
            logger.info("Deleted tranche", tranche=tranche.to_json())
        else:
            logger.warning("Attempted to delete non-existent tranche", tranche=tranche.to_json())

    # ----- unaudited_list ----- #
    def add_to_unaudited(self, tranche: Tranche, wr: WorkReport):
        state = self._get_state(tranche)
        if wr in state.unaudited_list:
            logger.warning("Work report already in unaudited list", wr_hash=Hash.blake2b(wr.encode()).hex()[:16])
            return
        state.unaudited_list.append(wr)
        self._save_state(tranche, state)
        logger.info("Added work report to unaudited list", wr_hash=Hash.blake2b(wr.encode()).hex()[:16])

    def rm_from_unaudited(self, tranche: Tranche, wr: WorkReport):
        state = self._get_state(tranche)
        try:
            state.unaudited_list.remove(wr)
            self._save_state(tranche, state)
            logger.info("Removed work report from unaudited list", wr_hash=Hash.blake2b(wr.encode()).hex()[:16])
        except ValueError:
            logger.warning("Work report not found in unaudited list for removal", wr_hash=Hash.blake2b(wr.encode()).hex()[:16])

    # ----- judgments ----- #
    def update_judgment(self, tranche: Tranche, wr: WorkReport, judgment: JudgmentRecord):
        state = self._get_state(tranche)
        encoded_wr = Bytes(wr.encode())
        state.judgments[encoded_wr] = judgment
        self._save_state(tranche, state)
        logger.info("Updated judgment for work report", wr_hash=Hash.blake2b(encoded_wr).hex()[:16])

    def get_judgment(self, tranche: Tranche, wr: WorkReport) -> JudgmentRecord | None:
        state = self._get_state(tranche)
        encoded_wr = Bytes(wr.encode())
        return state.judgments.get(encoded_wr)

    # ----- valid_set ----- #
    def add_to_valid_set(self, tranche: Tranche, wr: WorkReport):
        state = self._get_state(tranche)
        if wr in state.valid_set:
            logger.warning("Work report already in valid set", wr_hash=Hash.blake2b(wr.encode()).hex()[:16])
            return
        state.valid_set.append(wr)
        self._save_state(tranche, state)
        logger.info("Added work report to valid set", wr_hash=Hash.blake2b(wr.encode()).hex()[:16])

    # ----- invalid_set ----- #
    def add_to_invalid_set(self, tranche: Tranche, wr: WorkReport):
        state = self._get_state(tranche)
        if wr in state.invalid_set:
            logger.warning("Work report already in invalid set", wr_hash=Hash.blake2b(wr.encode()).hex()[:16])
            return
        state.invalid_set.append(wr)
        self._save_state(tranche, state)
        logger.info("Added work report to invalid set", wr_hash=Hash.blake2b(wr.encode()).hex()[:16])


tranche_store = TrancheStore()
