from typing import Dict

from tsrkit_types import Null, Uint
import bisect
import asyncio
from jam.logging import get_logger
from jam.types import Hash

from jam.types.audit.audit_tranche import (
    Tranche,
    TrancheState,
    AuditRecord,
    OptionalReports,
    ValidatorSignature,
    CoreReportHash
)

from jam.network.protocols.ce_144 import NoShow, Announcement
from jam.network.protocols.ce_145 import Judgment
from jam.types.protocol.core import ValidatorIndex, TrancheIndex
from jam.types.protocol.crypto import HeaderHash, Ed25519Public
from jam.types.work.report import WorkReport, WorkReportHash
from jam.block.extrinsics.disputes import Verdict, Culprit, Fault

logger = get_logger("tranche")


class TrancheStore:
    """ Persistent store for Tranches """
    _tranche_store: Dict[Tranche, TrancheState]
    _lock: bool

    def __init__(self) -> None:
        self._tranche_store = {}
        self._lock = asyncio.Lock()

    # ---------------------- Get whole tranche store -------------
    # just for debugging
    async def get_store(self) -> Dict[Tranche, TrancheState]:
        """ Return the entire tranche store safely. """
        async with self._lock:
            return self._tranche_store

    # --------------------- State Operations ---------------------

    def get_state(self, tranche: Tranche) -> TrancheState:
        """ Retrieve a TrancheState by Tranche object. """
        state = self._tranche_store.get(tranche)
        return state if state is not None else TrancheState.empty()

    def save_state(self, tranche: Tranche, state: TrancheState):
        """ Store TrancheState under its tranche key automatically."""
        self._tranche_store[tranche] = state

    # --------------------- Tranche Operations --------------------

    async def delete_tranche(self, tranche: Tranche):
        """ this function delete an individual (single) tranche """
        async with self._lock:
            header_hash = tranche.header_hash.hex()[:16]
            if tranche in self._tranche_store:
                del self._tranche_store[tranche]
                logger.info("Deleted tranche", tranche=tranche)
            else:
                logger.warning("Attempted to delete non-existent tranche", tranche=tranche)

    async def remove_block_history(self, header_hash: HeaderHash):
        async with self._lock:
            to_delete = [
                tranche for tranche in self._tranche_store
                if tranche.header_hash == header_hash
            ]

            for tranche in to_delete:
                del self._tranche_store[tranche]
                logger.debug("Deleted Block's tranche history", tranche=tranche)

            if to_delete:
                logger.debug("Deleted Block's entire tranche history")

    async def fetch_rep_tranche(self, judgment: Judgment):
        wr_hash = judgment.work_report_hash

        h_hash: HeaderHash | None = None
        rep_tranche: Tranche | None = None

        async with (self._lock):

            max_tranche_index : TrancheIndex | None = None
            for tranche, tranche_state in self._tranche_store.items():
                unaudited_list  = tranche_state.unaudited_list
                if len(unaudited_list) != 0:
                    for rep in unaudited_list:
                        if rep != Null:
                            if Hash.blake2b(rep.unwrap().encode()) == wr_hash:
                                h_hash = tranche.header_hash
                                if h_hash and h_hash != tranche.header_hash:
                                    raise ValueError("Found report in multiple blocks tranche!")

                                if max_tranche_index is not None:
                                    if tranche.tranche_index > max_tranche_index:
                                        max_tranche_index = tranche.tranche_index
                                        rep_tranche = Tranche(
                                            tranche_index= max_tranche_index,
                                            header_hash= tranche.header_hash
                                        )
                                else:
                                    rep_tranche = tranche

                else:
                    logger.debug(f"unaudited_list is empty for Tranche: {tranche}")
                    return

            if not rep_tranche:
                logger.error("No audit tranche found for given judgement's report", judgment=judgment)

        return rep_tranche

    # --------------------- WR Queue Access Operations ---------------------

    async def update_unaudited_list(self, tranche: Tranche, unaudited_reports: OptionalReports):
        async with self._lock:
            state = self._tranche_store.get(tranche)
            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            state.unaudited_list = unaudited_reports
            self._tranche_store[tranche] = state
            logger.info(f"Updated unaudited list for the tranches {tranche}")

    async def get_unaudited_list(self, tranche: Tranche):
        async with self._lock:
            state = self._tranche_store.get(tranche)
            if state:
                return state.unaudited_list
            else:
                logger.debug("State not found!")

    async def rm_from_unaudited(self, tranche: Tranche, wr_hash: WorkReportHash):
        async with self._lock:
            state = self._tranche_store.get(tranche)
            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return
            try:
                state = self._tranche_store.get(tranche)
                self._tranche_store[tranche] = state
                logger.debug("Removed work report from unaudited list", wr_hash=wr_hash.hex())
            except ValueError:
                logger.warning("Work report not found in unaudited list for removal", wr_hash=wr_hash.hex())

    # --------------------- Announcement Access Operations ---------------------

    async def records_announcement(self, tranche: Tranche, validator_index: ValidatorIndex, announce: Announcement):
        async with self._lock:
            from jam.settings import settings

            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche, so we create new one", tranche=tranche)
                # this condition comes because 2md validator taking time to start processing so
                # before initialzed its tranche state it received annfrom other, to save those ann
                # they have to build the tranche state

                # special condition
                if tranche.tranche_index == TrancheIndex(0):
                    new_state = TrancheState.empty()


                    for core_report in announce.assigned_reports:

                        new_state.records[core_report.report_hash] = AuditRecord.empty()

                        new_state.records[core_report.report_hash].announces.add(validator_index)

                        new_state.records[core_report.report_hash].no_shows.append(
                            NoShow(
                                validator_index=validator_index,
                                announcement=announce
                            )
                        )
                    self._tranche_store[tranche] = new_state

            else:

                for core_report in announce.assigned_reports:

                    if core_report.report_hash not in state.records:
                        state.records[core_report.report_hash] = AuditRecord.empty()

                        state.records[core_report.report_hash].announces.add(validator_index)

                        state.records[core_report.report_hash].no_shows.append(
                            NoShow(
                                validator_index=validator_index,
                                announcement=announce
                            )
                        )

                    else:
                        if validator_index not in state.records[core_report.report_hash].announces:

                            state.records[core_report.report_hash].announces.add(validator_index)

                            state.records[core_report.report_hash].no_shows.append(
                                NoShow(
                                    validator_index=validator_index,
                                    announcement=announce
                                )
                            )
                        else:
                            logger.info("Validator already exist in ANNOUNCEMENT")

                self._tranche_store[tranche] = state
        # logger.info("Recorded audit announcement", tranche=tranche, vi=validator_index, ann=announce)

    # --------------------- Judgement Operations ---------------------

    async def update_judgment(self,
        tranche: Tranche,
        judgment: Judgment,
        ed25519_public: Ed25519Public
        ):
        async with self._lock:

            validator_index = judgment.validator_index
            validity = judgment.validity
            wr_hash = judgment.work_report_hash
            edd2519_signature = judgment.ed25519_signature

            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            if wr_hash not in state.records:
                # it should be existed due to his announcement
                logger.debug("Unknown Report Judgement received", validator=validator_index)
                return

            else:
                try:
                    if validity == Uint[8](1):

                        validator_sign = ValidatorSignature(
                            validator_index=validator_index,
                            ed25519_public=ed25519_public,
                            ed25519_signature= edd2519_signature
                        )

                        # bisect.insort_left(true_votes_list, (validator_index, ed25519_public, edd2519_signature), key=lambda x: x[0])

                        state.records[wr_hash].true_votes.add(validator_sign)

                        no_shows_list = state.records[wr_hash].no_shows
                        found_no_show = False
                        for no_show in no_shows_list:
                            if no_show.validator_index == validator_index:
                                no_shows_list.remove(no_show)
                                found_no_show = True

                        if not found_no_show:
                            logger.error(f"work report exist in our state we don't have Announcements {wr_hash}")
                        else:
                            logger.info(f"Already judge the work report")

                    else:
                        validator_sign = ValidatorSignature(
                            validator_index=validator_index,
                            ed25519_public=ed25519_public,
                            ed25519_signature=edd2519_signature
                        )

                        # bisect.insort_left(true_votes_list, (validator_index, ed25519_public, edd2519_signature), key=lambda x: x[0])

                        state.records[wr_hash].false_votes.add(validator_sign)

                        no_shows_list = state.records[wr_hash].no_shows
                        for no_show in no_shows_list:
                            if no_show.validator_index == validator_index:
                                no_shows_list.remove(no_show)

                    self._tranche_store[tranche] = state
                    # logger.debug("Updated judgment for work report and remove no_show", judgment=judgment)

                except Exception as e:
                    logger.error(
                        f"failed to save judgment",
                        error=str(e),
                        error_type=type(e).__name__,
                    )

    # async def get_judgment(self, tranche: Tranche, wr_hash: WorkReportHash) -> AuditRecord | None:
    #     state = await self.get_state(tranche)
    #     return state.records.get(wr_hash)


    # --------------------- Validity Operations ---------------------

    async def add_to_audited_list(self, tranche: Tranche, c_w: CoreReportHash):
        async with self._lock:
            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            if c_w in state.audited_set:
                logger.warning("Work report already in valid set", c_w=c_w.work_report_hash)
                return

            state.audited_set.add(c_w)
            self._tranche_store[tranche] = state
            logger.info("Added work report to valid set", c_w=c_w.work_report_hash)

    async def get_audited_list(self, tranche: Tranche):
        async with self._lock:
            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            valid_list = state.audited_set

            if valid_list:
                return  valid_list
            else:
                logger.debug("no valid set exist in state ")

    async def add_to_invalid_set(self, tranche: Tranche, c_w: CoreReportHash):
        async with self._lock:
            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            if c_w in state.invalid_set:
                logger.warning("Work report already in invalid set", c_w=c_w.work_report_hash)
                return

            state.invalid_set.add(c_w)
            self._tranche_store[tranche] = state
            logger.debug("Added work report to invalid set", c_w=c_w.work_report_hash)

    async def get_invalid_list(self, tranche: Tranche):
        async with self._lock:
            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            invalid_list = state.invalid_set

            if invalid_list:
                return  invalid_list
            else:
                logger.debug("no valid set exist in state ")

#  --------------------- Dispute Operations ---------------------
    async def add_verdict(self, tranche: Tranche, verdict: Verdict):
        async with self._lock:

            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            for s_verdict in state.dispute.verdicts:
                target = s_verdict.target
                age = s_verdict.age
                votes = s_verdict.votes
                if target == verdict.target:
                    logger.warning(f"Verdict already exists")


            state.dispute.verdicts.append(verdict)

            self._tranche_store[tranche] = state
            logger.info(f"Add verdict for the report {verdict.target}")

    async def add_culprit(self, tranche: Tranche, culprit: Culprit):
        async with self._lock:

            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            for s_culprit in state.dispute.verdicts:
                target = s_culprit.target
                age = s_culprit.age
                votes = s_culprit.votes
                if target == culprit.target:
                    logger.warning(f"Culprit already exists")

            state.dispute.culprits.append(culprit)
            self._tranche_store[tranche] = state
            logger.info(f"Add Culprit for the report {culprit.target}")

    async def add_fault(self, tranche: Tranche, fault: Fault):
        async with self._lock:

            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            for s_fault in state.dispute.verdicts:
                target = s_fault.target
                age = s_fault.age
                votes = s_fault.votes
                if target == fault.target:
                    logger.warning(f"Faulter already exists")

            state.dispute.culprits.append(fault)
            self._tranche_store[tranche] = state
            logger.info(f"Add Faulter for the report {fault.target}")

tranche_store = TrancheStore()