from typing import Dict, Tuple
from tsrkit_types import Bool, Null
import bisect

from werkzeug.serving import af_unix

from jam.logging import get_logger
from jam.network.protocols.ce_144 import Announcement

from jam.types.audit.tranche import Tranche, TrancheState, AuditRecord, OptionalReports, ValidatorSignature
from jam.network.protocols.ce_144 import NoShow
from jam.network.protocols.ce_145 import Judgment

from jam.types.protocol.core import ValidatorIndex, CoreIndex, TrancheIndex
from jam.types.protocol.crypto import HeaderHash, Ed25519Signature, Ed25519Public
from jam.types.work.report import WorkReport, WorkReportHash
from jam.block.extrinsics.disputes import Verdict, Culprit, Fault

logger = get_logger("tranche")


class TrancheStore:
    """Persistent store for Tranches"""
    _tranche_store: Dict[Tranche, TrancheState]
    _lock: bool

    def __init__(self) -> None:
        self._tranche_store = {}
        self._lock = False

    # --------------------- State Operations ---------------------

    async def get_state(self, tranche: Tranche) -> TrancheState:
        """ Retrieve a TrancheState by Tranche object. """
        state = self._tranche_store.get(tranche)
        return state if state is not None else TrancheState.empty()

    async def save_state(self, tranche: Tranche, state: TrancheState):
        """ Store TrancheState under its tranche key automatically."""
        async with self._lock:
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

        async with self._lock:
            logger.debug("Fetching report tranche", judgment=judgment, store=self._tranche_store.items())

            max_tranche_index = None
            for tranche, tranche_state in self._tranche_store.items():
                unaudited_list  = tranche_state.unaudited_list
                if unaudited_list:
                    for rep in unaudited_list:
                        if rep is not Null:
                            if rep.report_hash == wr_hash:
                                # check condition
                                if h_hash and h_hash != tranche.header_hash:
                                    raise ValueError("Found report in multiple blocks tranche!")

                                if tranche.tranche_index > max_tranche_index:
                                    max_tranche_index = tranche.tranche_index
                                    rep_tranche = Tranche(
                                        tranche_index= max_tranche_index,
                                        header_hash= tranche.header_hash
                                    )
                                else:
                                    continue

                                # if rep_tranche and rep_tranche.tranche_index < tranche.tranche_index:
                                #     rep_tranche = tranche
                                # elif not rep_tranche:
                                #     rep_tranche = tranche

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

    async def records_announcement(self, tranche: Tranche, validator_index: ValidatorIndex, announce: Announcement):

        async with self._lock:

            state = self._tranche_store.get(tranche)

            for core, wr_hash in announce.assigned_reports:
                if wr_hash not in state.records:
                    state.records[wr_hash] = AuditRecord.empty()
                else:
                    # UPDATE VALIDATOR_INDEX
                    if validator_index not in state.records[wr_hash].announces:
                        state.records[wr_hash].announces.append(validator_index)
                    else:
                        logger.info("Validator already exist in ANNOUNCEMENT")

                    # UPDATE NO_SHOW
                    found = False
                    for no_show in state.records[wr_hash].no_shows:  # check for whole list of no_show
                        if validator_index in no_show:
                            found = True
                            break

                    if found:
                        logger.info("Validator's NO_SHOW already exist no need to add again")

                    else:
                        state.records[wr_hash].no_shows.append(
                            NoShow(
                                validator_index=validator_index,
                                announcement=announce
                            )
                        )

            self._tranche_store[tranche] = state
            logger.info("Recorded audit announcement", tranche=tranche, vi=validator_index, ann=announce.to_json())

    # --------------------- Judgement Operations ---------------------

    async def update_judgment(self,
        tranche: Tranche,
        judgment: Judgment,
        ed25519_public: Ed25519Public
        ):
        """ ... """

        validator_index = judgment.validator_index,
        validity = judgment.validity,
        wr_hash = judgment.work_report_hash,
        edd2519_signature = judgment.ed25519_signature,

        async with self._lock:
            state = self._tranche_store.get(tranche)

            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            if wr_hash not in state.records:
                # it should be exist due to his announcement
                logger.debug("Unknown Report Judgement received", validator=validator_index)
                return

            if judgment:

                # validator_sign = ValidatorSignature(
                #     validator_index=ValidatorIndex,
                #     ed25519_public=ed25519_public,
                #     signature= edd2519_signature
                # )

                true_votes_list = state.records[wr_hash].true_votes
                bisect.insort_left(true_votes_list, (validator_index, ed25519_public, edd2519_signature), key=lambda x: x[0])

                # state.records[wr_hash].true_votes.append(validator_sign)

                no_shows_list = state.records[wr_hash].no_shows
                for no_show in no_shows_list:
                    if no_show[0] == validator_index:
                        no_shows_list.remove(no_show)

            else:
                # validator_sign = ValidatorSignature(
                #     validator_index=ValidatorIndex,
                #     ed25519_public=ed25519_public,
                #     signature=edd2519_signature
                # )

                true_votes_list = state.records[wr_hash].false_votes

                bisect.insort_left(true_votes_list, (validator_index, ed25519_public, edd2519_signature), key=lambda x: x[0])


                # state.records[wr_hash].false_votes.append(validator_sign)

                no_shows_list = state.records[wr_hash].no_shows
                for no_show in no_shows_list:
                    if no_show[0] == validator_index:
                        no_shows_list.remove(no_show)

            self._tranche_store[tranche] = state

            logger.debug("Updated judgment for work report", judgment=judgment)

    async def get_judgment(self, tranche: Tranche, wr_hash: WorkReportHash) -> AuditRecord | None:
        state = await self.get_state(tranche)
        return state.records.get(wr_hash)


    # --------------------- Validity Operations ---------------------

    async def add_to_valid_set(self, tranche: Tranche, c_w: Tuple[CoreIndex, WorkReportHash]):
        async with self._lock:
            state = self._tranche_store.get(tranche)
            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            if c_w in state.valid_set:
                logger.warning("Work report already in valid set", c_w=c_w[1].hex())
                return

            state.valid_set.append(c_w)
            self._tranche_store[tranche] = state
            logger.debug("Added work report to valid set", c_w=c_w[1].hex())

    async def add_to_invalid_set(self, tranche: Tranche, c_w: Tuple[CoreIndex, WorkReportHash]):
        async with self._lock:
            state = self._tranche_store.get(tranche)
            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            if c_w in state.invalid_set:
                logger.warning("Work report already in invalid set", c_w=c_w[1].hex())
                return

            state.invalid_set.append(c_w)
            self._tranche_store[tranche] = state
            logger.debug("Added work report to invalid set", c_w=c_w[1].hex())

    #  --------------------- Dispute Operations ---------------------
    def add_verdict(self, tranche: Tranche, verdict: Verdict):
        state = self.get_state(tranche)

        exist = False
        for target, age, votes in state.dispute.verdicts:
            if target == verdict.target:
                exist = True

        if not exist:
            state.dispute.verdicts.append(verdict)

        self.save_state(tranche, state)

    def add_culprit(self, tranche: Tranche, culprit: Culprit):
        state = self.get_state(tranche)

        exist = False
        for target, age, votes in state.dispute.verdicts:
            if target == culprit.target:
                exist = True

        if not exist:
            state.dispute.verdicts.append(culprit)

        state.dispute.culprits.append(culprit)
        self.save_state(tranche, state)

    def add_fault(self, tranche: Tranche, fault: Fault):
        state = self.get_state(tranche)

        exist = False
        for target, age, votes in state.dispute.verdicts:
            if target == fault.target:
                exist = True

        if not exist:
            state.dispute.verdicts.append(fault)

        state.dispute.faults.append(fault)
        self.save_state(tranche, state)

tranche_store = TrancheStore()
