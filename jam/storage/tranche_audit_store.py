from typing import Dict
from tsrkit_types import Null, Uint, TypedVector
import asyncio
from jam.log_setup import node_logger

from jam.models.audit.audit_tranche import (
    Tranche,
    TrancheState,
    AuditRecord,
    OptionalReports,
    JudgmentData,
    CoreReport,
)
from jam.network.protocols.ce_144 import NoShow, Announcement
from jam.network.protocols.ce_145 import Judgment
from jam.models.protocol.core import ValidatorIndex, TrancheIndex
from jam.models.protocol.crypto import HeaderHash, Ed25519Public
from jam.models.work.report import WorkReportHash

logger = node_logger


class TrancheStore:
    """Persistent store for Tranche"""

    _tranche_store: Dict[Tranche, TrancheState]
    _lock: asyncio.Lock

    def __init__(self) -> None:
        self._tranche_store = {}
        self._lock = asyncio.Lock()

    # ---------------------- Get whole tranche store -------------
    async def get_store(self) -> Dict[Tranche, TrancheState]:
        """Return the entire tranche store safely."""
        async with self._lock:
            return self._tranche_store

    # --------------------- State Operations ---------------------
    async def get_state(self, tranche: Tranche) -> TrancheState:
        async with self._lock:
            """Retrieve a TrancheState by Tranche object."""
            state = self._tranche_store.get(tranche)
            return state if state is not None else TrancheState.empty()

    async def save_state(self, tranche: Tranche, state: TrancheState):
        """Store TrancheState under its tranche key automatically."""
        async with self._lock:
            self._tranche_store[tranche] = state

    # --------------------- Tranche Operations --------------------
    async def delete_tranche(self, tranche: Tranche):
        """this function delete an individual (single) tranche"""
        async with self._lock:
            header_hash = tranche.header_hash.hex()[:16]
            if tranche in self._tranche_store:
                del self._tranche_store[tranche]
                logger.debug("Deleted tranche", tranche=tranche)
            else:
                logger.warning("Attempted to delete non-existent tranche", tranche=tranche)

    async def remove_block_history(self, header_hash: HeaderHash):
        async with self._lock:
            to_delete = [
                tranche for tranche in self._tranche_store if tranche.header_hash == header_hash
            ]

            for tranche in to_delete:
                del self._tranche_store[tranche]
                logger.debug("Deleted Block's tranche history", tranche=tranche)

            if to_delete:
                logger.debug("Deleted Block's entire tranche history")

    async def fetch_rep_tranche(self, judgment: Judgment):
        """Fetch Work Report HASH Tranche (tranche_index, header_hash)"""
        wr_hash = judgment.work_report_hash

        async with self._lock:
            # collect matching tranches
            list_tranche = [
                tranche
                for tranche, tranche_state in self._tranche_store.items()
                if wr_hash in tranche_state.records
                and judgment.validator_index in tranche_state.records[wr_hash].announces
            ]

            if not list_tranche:
                return None

            # return tranche with max index
            return max(list_tranche, key=lambda t: t.tranche_index)

    # --------------------- WR Queue Access Operations ---------------------
    async def update_unaudited_list(self, tranche: Tranche, unaudited_reports: OptionalReports):
        async with self._lock:
            state = self._tranche_store.get(tranche)
            if not state:
                logger.error("No state for given tranche, update_unaudited_list", tranche=tranche)
                return

            state.unaudited_list = unaudited_reports
            self._tranche_store[tranche] = state
            logger.debug(f"Updated unaudited list for the tranches {tranche}")

    async def get_unaudited_list(self, tranche: Tranche):
        async with self._lock:
            state = self._tranche_store.get(tranche)
            if state:
                return state.unaudited_list
            logger.error("State not found!", tranche=tranche)
            return OptionalReports.empty()

    # --------------------- Announcement Access Operations ---------------------
    async def records_announcement(
        self, tranche: Tranche, validator_index: ValidatorIndex, announce: Announcement
    ):
        async with self._lock:
            state = self._tranche_store.get(tranche)

            try:
                if not state:
                    logger.warning(
                        "No state for given tranche, so we create new one", tranche=tranche
                    )

                    if tranche.tranche_index == TrancheIndex(0):
                        new_state = TrancheState.empty()

                        for c_r in announce.assigned_reports:
                            new_state.records[c_r.report_hash] = AuditRecord.empty()
                            new_state.records[c_r.report_hash].announces.add(validator_index)
                            new_state.records[c_r.report_hash].no_shows.append(
                                NoShow(validator_index=validator_index, announcement=announce)
                            )

                        self._tranche_store[tranche] = new_state
                        return

                    prev_tranche = Tranche(
                        tranche_index=tranche.tranche_index - TrancheIndex(1),
                        header_hash=tranche.header_hash,
                    )

                    prev_state = self._tranche_store.get(prev_tranche)
                    new_state = prev_state.carry_forward()
                    for c_r in announce.assigned_reports:
                        new_state.records[c_r.report_hash].announces.add(validator_index)
                        new_state.records[c_r.report_hash].no_shows.append(
                            NoShow(validator_index=validator_index, announcement=announce)
                        )
                    self._tranche_store[tranche] = new_state
                    return

                for c_r in announce.assigned_reports:
                    if c_r.report_hash not in state.records:
                        state.records[c_r.report_hash] = AuditRecord.empty()
                        state.records[c_r.report_hash].announces.add(validator_index)
                        state.records[c_r.report_hash].no_shows.append(
                            NoShow(validator_index=validator_index, announcement=announce)
                        )

                    else:
                        if validator_index not in state.records[c_r.report_hash].announces:
                            state.records[c_r.report_hash].announces.add(validator_index)
                            state.records[c_r.report_hash].no_shows.append(
                                NoShow(validator_index=validator_index, announcement=announce)
                            )
                        else:
                            logger.info("Validator already exist in ANNOUNCEMENT")

                self._tranche_store[tranche] = state
                return

            except KeyError as e:
                logger.error(
                    "Failed to save Announcements due to missing key",
                    tranche=tranche,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

            except Exception as e:
                logger.exception(
                    "Unexpected error while saving Announcements",
                    tranche=tranche,
                )
                raise

    # --------------------- Judgement Operations ---------------------
    async def update_judgment(
        self, tranche: Tranche, ed25519_public: Ed25519Public, judgment: Judgment
    ):
        """
        This function updates validator judgments (True or False) based on their refinements and tranche index.
        """

        async with self._lock:
            validator_index = judgment.validator_index
            validity = judgment.validity
            wr_hash = judgment.work_report_hash
            ed25519_signature = judgment.ed25519_signature

            state = self._tranche_store.get(tranche)

            if not state:
                logger.error("No state for given tranche", tranche=tranche)
                return

            if wr_hash not in state.records:
                logger.error(
                    "Unknown Report Judgement received", validator=validator_index, wr_hash=wr_hash
                )
                return

            record = state.records[wr_hash]
            announcements = record.announces
            true_votes = record.true_votes
            false_votes = record.false_votes

            judge_info = JudgmentData(
                epoch_index=judgment.epoch_index,
                validator_index=validator_index,
                ed25519_public=ed25519_public,
                ed25519_signature=ed25519_signature,
            )

            try:
                if validator_index in true_votes:
                    logger.info(
                        "Validator already gave True judgment for work report",
                        wr_hash=wr_hash.hex(),
                        validator=validator_index,
                    )

                    if validity == Uint[8](0):
                        true_votes.remove(validator_index)
                        false_votes.add(judge_info)
                    return

                if validator_index in false_votes:
                    logger.info(
                        "Validator already gave False judgment for work report",
                        wr_hash=wr_hash.hex(),
                        validator=validator_index,
                    )

                    if validity == Uint[8](1):
                        false_votes.remove(validator_index)
                        true_votes.add(judge_info)
                    return

                # first time judgment
                target_set = true_votes if validity == Uint[8](1) else false_votes
                target_set.add(judge_info)
                no_shows_list = record.no_shows

                if validator_index in announcements:
                    for no_show in list(no_shows_list):
                        if no_show.validator_index == validator_index:
                            no_shows_list.remove(no_show)

                else:
                    logger.info(
                        "Judgment received without prior announcement",
                        validator=validator_index,
                        wr_hash=wr_hash.hex(),
                    )

                self._tranche_store[tranche] = state
                logger.debug(
                    "Updated judgment for work report and adjusted no_show",
                    judgment=judgment,
                )

            except Exception as e:
                logger.exception(
                    "Failed to save judgment in tranche store",
                    wr_hash=wr_hash.hex(),
                )
                raise

    # --------------------- Validity Operations ---------------------
    async def add_to_audited_list(self, tranche: Tranche, c_r: CoreReport):
        try:
            async with self._lock:
                state = self._tranche_store.get(tranche)

                if not state:
                    logger.error("No State found for given Tranche", tranche=tranche)
                    return

                if c_r in state.audited_list:
                    logger.debug("Work Report already in Audited list", c_r=c_r.work_report)
                    return

                state.audited_list.append(c_r)
                self._tranche_store[tranche] = state
                logger.debug("Added work report to Audited list", c_r=c_r.work_report)

        except Exception as e:
            logger.exception(
                "Unexpected error while adding to audited list",
                tranche=tranche,
                c_r=c_r,
                error=str(e),
            )

    async def get_audited_list(self, tranche: Tranche) -> TypedVector[CoreReport]:
        async with self._lock:
            state = self._tranche_store.get(tranche)

            if not state:
                logger.error(
                    "Tranche state not found while retrieving audited list", tranche=tranche
                )
                return TypedVector[CoreReport]([])
            valid_list = state.audited_list

            if valid_list:
                return valid_list
            else:
                logger.error("Audited list is empty for tranche state", tranche=tranche)
                return TypedVector[CoreReport]([])


tranche_store = TrancheStore()
