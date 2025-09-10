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

from jam.types.protocol.core import ValidatorIndex, CoreIndex, TrancheIndex
from jam.types.protocol.crypto import HeaderHash, Ed25519Signature, Ed25519Public
from jam.types.work.report import WorkReport, WorkReportHash
from jam.block.extrinsics.disputes import Verdict, Culprit, Fault
from tests.unit.trie.test_update import test_reinsert_same_value_no_change

logger = get_logger("tranche")


class TrancheStore:
    """Persistent store for Tranches"""
    _tranche_store: Dict[Tranche, TrancheState]
    _lock: bool

    def __init__(self) -> None:
        self._tranche_store = {}
        self._lock = asyncio.Lock()

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
        async with self._lock:
            if tranche in self._tranche_store:
                del self._tranche_store[tranche]
                logger.info("Deleted tranche", tranche=tranche)
            else:
                logger.warning("Attempted to delete non-existent tranche", tranche=tranche)

    async def remove_block_history(self, header_hash: HeaderHash):
        async with self._lock:
            for tranche in self._tranche_store:
                if tranche.header_hash == header_hash:
                    del  self._tranche_store[tranche]
                    logger.debug("Deleted Block's tranche history", tranche=tranche)

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
                            if Hash.blake2b(rep.encode()) == wr_hash:
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

            logger.debug(f"rep_tranche {rep_tranche.tranche_index}, {tranche.header_hash}")

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
            state = self.get_state(tranche)
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

    def records_announcement(self, tranche: Tranche, validator_index: ValidatorIndex, announce: Announcement):

        from jam.settings import settings

        state = self._tranche_store.get(tranche)


        # optimized
        if not state:
            logger.warning("No state for given tranche, so we create new one", tranche=tranche)

            # Tranche 0 empty state initialize
            new_state = TrancheState.empty()

            for core_report in announce.assigned_reports:

                if core_report.report_hash not in new_state.records:
                    new_state.records[core_report.report_hash] = AuditRecord.empty()

                    # UPDATE VALIDATOR_INDEX
                    if validator_index not in new_state.records[core_report.report_hash].announces:
                        new_state.records[core_report.report_hash].announces.append(validator_index)
                    else:
                        logger.info("Validator already exist in ANNOUNCEMENT")

                    # UPDATE NO_SHOW
                    found = False
                    for no_show in new_state.records[core_report.report_hash].no_shows:  # check for whole list of no_show
                        if validator_index in no_show:
                            found = True
                            break

                    if found:
                        logger.info("Validator's NO_SHOW already exist no need to add again")

                    else:
                        new_state.records[core_report.report_hash].no_shows.append(
                            NoShow(
                                validator_index=validator_index,
                                announcement=announce
                            )
                        )

            self._tranche_store[tranche] = new_state
            # Tranche 0 empty state initialized

        else:

            for core_report in announce.assigned_reports:

                if core_report.report_hash not in state.records:
                    state.records[core_report.report_hash] = AuditRecord.empty()

                    # UPDATE VALIDATOR_INDEX
                    if validator_index not in state.records[core_report.report_hash].announces:
                        state.records[core_report.report_hash].announces.append(validator_index)
                    else:
                        logger.info("Validator already exist in ANNOUNCEMENT")

                    # UPDATE NO_SHOW
                    found = False
                    for no_show in state.records[core_report.report_hash].no_shows:  # check for whole list of no_show
                        if validator_index in no_show:
                            found = True
                            break

                    if found:
                        logger.info("Validator's NO_SHOW already exist no need to add again")

                    else:
                        state.records[core_report.report_hash].no_shows.append(
                            NoShow(
                                validator_index=validator_index,
                                announcement=announce
                            )
                        )

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

            if wr_hash in state.records.values():
                # it should be existed due to his announcement
                logger.debug("Unknown Report Judgement received", validator=validator_index)
                return
            try:

                if validity == Uint[8](1):

                    validator_sign = ValidatorSignature(
                        validator_index=validator_index,
                        ed25519_public=ed25519_public,
                        ed25519_signature= edd2519_signature
                    )

                    # bisect.insort_left(true_votes_list, (validator_index, ed25519_public, edd2519_signature), key=lambda x: x[0])

                    state.records[wr_hash].true_votes.append(validator_sign)

                    no_shows_list = state.records[wr_hash].no_shows
                    for no_show in no_shows_list:
                        if no_show.validator_index == validator_index:
                            no_shows_list.remove(no_show)

                else:
                    validator_sign = ValidatorSignature(
                        validator_index=validator_index,
                        ed25519_public=ed25519_public,
                        ed25519_signature=edd2519_signature
                    )

                    # bisect.insort_left(true_votes_list, (validator_index, ed25519_public, edd2519_signature), key=lambda x: x[0])

                    state.records[wr_hash].false_votes.append(validator_sign)

                    no_shows_list = state.records[wr_hash].no_shows
                    for no_show in no_shows_list:
                        if no_show.validator_index == validator_index:
                            no_shows_list.remove(no_show)

                self._tranche_store[tranche] = state
                logger.debug("Updated judgment for work report", judgment=judgment)

            except Exception as e:
                logger.error(
                    f"failed to judgments judgment",
                    error=str(e),
                    error_type=type(e).__name__,
                )

    # async def get_judgment(self, tranche: Tranche, wr_hash: WorkReportHash) -> AuditRecord | None:
    #     state = await self.get_state(tranche)
    #     return state.records.get(wr_hash)


    # --------------------- Validity Operations ---------------------

    async def add_to_valid_set(self, tranche: Tranche, c_w: CoreReportHash):
        async with self._lock:
            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            if c_w in state.valid_set:
                logger.warning("Work report already in valid set", c_w=c_w.work_report_hash)
                return

            state.valid_set.append(c_w)
            self._tranche_store[tranche] = state
            logger.info("Added work report to valid set", c_w=c_w.work_report_hash)

    async def get_valid_list(self, tranche: Tranche):
        async with self._lock:
            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            valid_list = state.valid_set

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

            state.invalid_set.append(c_w)
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

            self.save_state(tranche, state)
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
            self.save_state(tranche, state)
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
            self.save_state(tranche, state)
            logger.info(f"Add Faulter for the report {fault.target}")

tranche_store = TrancheStore()