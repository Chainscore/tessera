from typing import Dict
from tsrkit_types import Bool, Option, TypedVector

from jam.logging import get_logger

from jam.types.audit.tranche import Tranche, TrancheState, AuditRecord, Announcement
from jam.types.protocol.core import ValidatorIndex
from jam.types.protocol.crypto import HeaderHash
from jam.types.work.report import WorkReport, WorkReportHash

logger = get_logger("tranche")


class TrancheStore:
    """Persistent store for Tranches"""
    _tranche_store: Dict[Tranche, TrancheState]

    def __init__(self) -> None:
        self._tranche_store = {}

    # -------------------- RELATED STATES ----------------------------------
    def get_state(self, tranche: Tranche) -> TrancheState:
        """ Retrieve a TrancheState by Tranche object. """
        state = self._tranche_store.get(tranche)
        return state if state is not None else TrancheState.empty()


    def save_state(self, tranche: Tranche, state: TrancheState):
        """ Store TrancheState under its tranche key automatically."""
        self._tranche_store[tranche] = state

    # ----------------------------------- RELATED TRANCHE (HEADER AND TRANCHE_INDEX) --------------------------------------------------------------

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
    # done
    def add_to_unaudited(self, tranche: Tranche, unaudited_reports: TypedVector[Option[WorkReport]]):
        state = self.get_state(tranche)

        state.unaudited_list = unaudited_reports
        self.save_state(tranche=tranche, state=state)
        logger.info(f"Updated unaudited list for specific tranches {tranche.tranche_index}")

    def get_unaudited_list(self, tranche: Tranche):
        state = self._tranche_store.get(tranche)
        if state:
            return state.unaudited_list
        else:
            logger.info("Empty unaudited list")

    # ----------------------------------------------------------------------------------------

    def rm_from_unaudited(self, tranche: Tranche, wr_hash: WorkReportHash):
        state = self.get_state(tranche)
        try:
            state.unaudited_list.remove(wr_hash)
            self.save_state(tranche, state)
            logger.info("Removed work report from unaudited list", wr_hash=wr_hash)
        except ValueError:
            logger.warning("Work report not found in unaudited list for removal", wr_hash=wr_hash)


    # ----------------------------- ANNOUNCEMENT'S FUNCTION ------------------------------------------------------------
    def add_announce(self, tranche: Tranche, wr_hash: WorkReportHash, validator_index:ValidatorIndex) :
        state = self.get_state(tranche)
        if wr_hash not in state.judgments:
            state.judgments[wr_hash] = AuditRecord.empty()
        state.judgments[wr_hash].announces.append(validator_index)
        state.judgments[wr_hash].no_votes.append(validator_index)
        self.save_state(tranche, state)
        logger.info("Updated announcement for work report", wr_hash =wr_hash)

    def add_set_announcement(self, tranche: Tranche, validator_index: ValidatorIndex, assign_r: Announcement):
        state = self.get_state(tranche)
        if validator_index not in state.validator_announcement:
            state.validator_announcement[validator_index] = assign_r
        self._save_state(tranche, state)
        logger.info("Updated announcement for validaot", validator_index)

    def get_set_announcement(self, tranche: Tranche, validator_index: ValidatorIndex):
        state = self._tranche_store.get(tranche)
        if state:
            return state.validator_announcement.get(validator_index)
        else:
            logger.info("NO validator announcement save")


    # ----------------------------- JUDGMENT'S FUNCTION ----------------------------------------------------------------

    def update_judgment(self, tranche: Tranche, wr_hash: WorkReportHash, judgment: Bool, validator_index: ValidatorIndex):
        state = self.get_state(tranche)

        if wr_hash not in state.judgments:
            state.judgments[wr_hash] = AuditRecord.empty()

        if judgment:
            state.judgments[wr_hash].true_votes.append(validator_index)
            state.judgments[wr_hash].no_votes.remove(validator_index)


        else:
            state.judgments[wr_hash].false_votes.append(validator_index)
            state.judgments[wr_hash].no_votes.remove(validator_index)


        self.save_state(tranche, state)
        logger.info("Updated judgment for work report", wr_hash=wr_hash)

    def get_judgment(self, tranche: Tranche, wr_hash: WorkReportHash) -> AuditRecord | None:
        state = self.get_state(tranche)
        return state.judgments.get(wr_hash)


    # --------------------- VALID AND INVALID FUNCTIONS ----------------------------------------------------------------

    def add_to_valid_set(self, tranche: Tranche, wr_hash: WorkReportHash):
        state = self.get_state(tranche)
        if wr_hash in state.valid_set:
            logger.warning("Work report already in valid set", wr_hash=wr_hash)
            return
        state.valid_set.append(wr_hash)
        self.save_state(tranche, state)
        logger.info("Added work report to valid set", wr_hash=wr_hash)

    def add_to_invalid_set(self, tranche: Tranche, wr_hash: WorkReportHash):
        state = self.get_state(tranche)
        if wr_hash in state.invalid_set:
            logger.warning("Work report already in invalid set", wr_hash=wr_hash)
            return
        state.invalid_set.append(wr_hash)
        self.save_state(tranche, state)
        logger.info("Added work report to invalid set", wr_hash=wr_hash)


tranche_store = TrancheStore()
