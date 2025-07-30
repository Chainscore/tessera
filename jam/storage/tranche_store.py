from typing import Dict
from tsrkit_types import Bool, Option

from jam.logging import get_logger

from jam.types.audit.tranche import Tranche, TrancheState, JudgmentRecord
from jam.types.protocol.core import ValidatorIndex
from jam.types.protocol.crypto import HeaderHash
from jam.types.work.report import WorkReport, WorkReportHash

logger = get_logger("tranche")


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



    # ----------------------------------- RELATED TRANCHE --------------------------------------------------------------

    def get_tranche_index(self, header_hash: HeaderHash):
        for tranche in self._tranche_store:
            if tranche.header_hash == header_hash:
                return tranche.tranche_index
            else:
                logger.info("There is no header hash exist in tranche store")


    def delete_tranche(self, tranche: Tranche):
        if tranche in self._tranche_store:
            del self._tranche_store[tranche]
            logger.info("Deleted tranche", tranche=tranche.to_json())
        else:
            logger.warning("Attempted to delete non-existent tranche", tranche=tranche.to_json())

    # ---------------------------------- UNAUDITED LIST -----------------------------------
    def add_to_unaudited(self, tranche: Tranche, p_a_r: list[Option[WorkReport]]):
        state = self._get_state(tranche)

        if tranche.tranche_index == 0:
            state.unaudited_list = p_a_r
            self._save_state(tranche=tranche, state=state)
            return


        # for wr in p_a_r:
        #     if wr == Null:
        #         state.unaudited_list.append(Null)
        #     elif wr is not Null and wr in state.unaudited_list:
        #         logger.warning("Work report already in unaudited list", wr_hash=WorkReportHash)
        #         return
        #     else:
        #         state.unaudited_list.append(wr)
        #
        # self._save_state(tranche, state)
        # logger.info("Added work report to unaudited list", wr_hash=WorkReportHash)

    def get_unaudit_list(self, tranche: Tranche):
        state = self._tranche_store.get(tranche)
        if state:
            return state.unaudited_list
        else:
            logger.info("Empty unaudit list")



    def rm_from_unaudited(self, tranche: Tranche, wr_hash: WorkReportHash):
        state = self._get_state(tranche)
        try:
            state.unaudited_list.remove(wr_hash)
            self._save_state(tranche, state)
            logger.info("Removed work report from unaudited list", wr_hash=wr_hash)
        except ValueError:
            logger.warning("Work report not found in unaudited list for removal", wr_hash=wr_hash)


    # ----------------------------- ANNOUNCEMENT'S FUNCTION ------------------------------------------------------------
    def add_announce(self, tranche: Tranche, wr_hash: WorkReportHash, validator_index:ValidatorIndex) :
        state = self._get_state(tranche)
        if wr_hash not in state.judgments:
            state.judgments[wr_hash] = JudgmentRecord.empty()
        state.judgments[wr_hash].announces.append(validator_index)
        self._save_state(tranche, state)
        logger.info("Updated announcement for work report", wr_hash =wr_hash)


    # ----------------------------- JUDGMENT'S FUNCTION ----------------------------------------------------------------

    def update_judgment(self, tranche: Tranche, wr_hash: WorkReportHash, judgment: Bool, validator_index: ValidatorIndex):
        state = self._get_state(tranche)

        if wr_hash not in state.judgments:
            state.judgments[wr_hash] = JudgmentRecord.empty()

        if judgment:
            state.judgments[wr_hash].true_votes.append(validator_index)
        else:
            state.judgments[wr_hash].false_votes.append(validator_index)

        self._save_state(tranche, state)
        logger.info("Updated judgment for work report", wr_hash=wr_hash)

    def get_judgment(self, tranche: Tranche, wr_hash: WorkReportHash) -> JudgmentRecord | None:
        state = self._get_state(tranche)
        return state.judgments.get(wr_hash)


    # --------------------- VALID AND INVALID FUNCTIONS ----------------------------------------------------------------


    def add_to_valid_set(self, tranche: Tranche, wr_hash: WorkReportHash):
        state = self._get_state(tranche)
        if wr_hash in state.valid_set:
            logger.warning("Work report already in valid set", wr_hash=wr_hash)
            return
        state.valid_set.append(wr_hash)
        self._save_state(tranche, state)
        logger.info("Added work report to valid set", wr_hash=wr_hash)

    def add_to_invalid_set(self, tranche: Tranche, wr_hash: WorkReportHash):
        state = self._get_state(tranche)
        if wr_hash in state.invalid_set:
            logger.warning("Work report already in invalid set", wr_hash=wr_hash)
            return
        state.invalid_set.append(wr_hash)
        self._save_state(tranche, state)
        logger.info("Added work report to invalid set", wr_hash=wr_hash)


tranche_store = TrancheStore()
