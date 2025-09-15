import asyncio
from typing import Dict

from jam.logging import node_logger
from jam.network.protocols.ce_144 import Announcement
from jam.network.protocols.ce_145 import Judgment

from jam.types.audit.tranche import Tranche, TrancheState, AuditRecord, OptionalReports

from jam.types.protocol.core import ValidatorIndex
from jam.types.protocol.crypto import HeaderHash
from jam.types.work.report import WorkReport, WorkReportHash

logger = node_logger


class TrancheStore:
    """Persistent store for Tranches"""
    _tranche_store: Dict[Tranche, TrancheState]
    _lock: asyncio.Lock

    def __init__(self) -> None:
        self._tranche_store = {}
        self._lock = asyncio.Lock()

    # --------------------- State Access Operations (Lock Free) ---------------------

    async def get_state(self, tranche: Tranche) -> TrancheState:
        """ Retrieve a TrancheState by Tranche object. """
        async with self._lock:
            state = self._tranche_store.get(tranche)
            return state if state is not None else TrancheState.empty()


    async def save_state(self, tranche: Tranche, state: TrancheState):
        """ Store TrancheState under its tranche key automatically."""
        async with self._lock:
            self._tranche_store[tranche] = state


    # --------------------- Tranche Access Operations ---------------------

    async def get_tranche_index(self, header_hash: HeaderHash):
        async with self._lock:
            for tranche in self._tranche_store:
                if tranche.header_hash == header_hash:
                    return tranche.tranche_index
                else:
                    logger.info("There is no header hash exist in tranche store")


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

    async def fetch_rep_tranche(self, judgment = Judgment):
        wr_hash = judgment.work_report_hash
        vi = judgment.validator_index

        h_hash: HeaderHash | None = None
        rep_tranche: Tranche | None = None

        async with self._lock:
            logger.debug("Fetching report tranche", judgment=judgment, store=self._tranche_store.items())
            for tranche, tranche_state in self._tranche_store.items():
                anns: Announcement | None  = tranche_state.announcements.get(vi, None)

                if anns:
                    for rep in anns.assigned_reports:
                        if rep.report_hash == wr_hash:
                            if h_hash and h_hash != tranche.header_hash:
                                raise ValueError("Found report in multiple blocks tranche!")

                            h_hash = tranche.header_hash
                            if rep_tranche and rep_tranche.tranche_index < tranche.tranche_index:
                                rep_tranche = tranche
                            elif not rep_tranche:
                                rep_tranche = tranche

        if not rep_tranche:
            logger.error("No audit tranche found for given judgement's report", judgment=judgment.to_json())

        return rep_tranche

    # --------------------- WR Queue Access Operations ---------------------

    async def add_to_unaudited(self, tranche: Tranche, unaudited_reports: OptionalReports):
        async with self._lock:
            state = self._tranche_store.get(tranche)
            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            state.unaudited_list = unaudited_reports
            self._tranche_store[tranche] = state
            logger.info("Updated unaudited list.", tranche=tranche)

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
                state.unaudited_list.remove(wr_hash)
                self._tranche_store[tranche] = state
                logger.debug("Removed work report from unaudited list", wr_hash=wr_hash.hex())
            except ValueError:
                logger.warning("Work report not found in unaudited list for removal", wr_hash=wr_hash.hex())



    # --------------------- Announcement Access Operations ---------------------

    async def record_announcement(self, tranche: Tranche, validator_index: ValidatorIndex, ann: Announcement):
        from jam.settings import settings
        async with self._lock:
            state = self._tranche_store.get(tranche)
            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            if validator_index not in state.announcements:
                state.announcements[validator_index] = ann

            for rep in ann.assigned_reports:
                wr_hash = rep.report_hash
                if wr_hash not in state.records:
                    state.records[wr_hash] = AuditRecord.empty()

                if validator_index not in state.records[wr_hash].announces:
                    state.records[wr_hash].announces.append(validator_index)

                if validator_index not in state.records[wr_hash].no_votes:
                    state.records[wr_hash].no_votes.append(validator_index)

            self._tranche_store[tranche] = state
            logger.info("Recorded audit announcement", tranche=tranche, vi=validator_index, ann=ann.to_json())

    async def get_set_announcement(self, tranche: Tranche, validator_index: ValidatorIndex):
        async  with self._lock:
            state = self._tranche_store.get(tranche)
            if state:
                return state.announcements.get(validator_index)
            else:
                logger.warning("No state for given tranche", tranche=tranche)


    # --------------------- Judgement Access Operations ---------------------

    async def update_judgment(self, tranche: Tranche, judgment: Judgment):
        from jam.settings import settings

        validator_index = judgment.validator_index
        wr_hash = judgment.work_report_hash

        async  with self._lock:
            state = self._tranche_store.get(tranche)
            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            if wr_hash not in state.records:
                logger.debug("Unknown Report Judgement received", validator=validator_index)
                return

            if judgment.validity:
                state.records[wr_hash].true_votes.append(validator_index)
                state.records[wr_hash].no_votes.remove(validator_index)


            else:
                state.records[wr_hash].false_votes.append(validator_index)
                state.records[wr_hash].no_votes.remofve(validator_index)

            self._tranche_store[tranche] = state
            logger.debug("Updated judgment for work report", judgment=judgment.to_json())

    async def get_judgment(self, tranche: Tranche, wr_hash: WorkReportHash) -> AuditRecord | None:
        state = await self.get_state(tranche)
        return state.records.get(wr_hash)



    # --------------------- Validity Access Operations ---------------------

    async def add_to_valid_set(self, tranche: Tranche, wr_hash: WorkReportHash):
        async with self._lock:
            state = self._tranche_store.get(tranche)
            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            if wr_hash in state.valid_set:
                logger.warning("Work report already in valid set", wr_hash=wr_hash.hex())
                return

            state.valid_set.append(wr_hash)
            self._tranche_store[tranche] = state
            logger.debug("Added work report to valid set", wr_hash=wr_hash.hex())

    async def add_to_invalid_set(self, tranche: Tranche, wr_hash: WorkReportHash):
        async with self._lock:
            state = self._tranche_store.get(tranche)
            if not state:
                logger.warning("No state for given tranche", tranche=tranche)
                return

            if wr_hash in state.invalid_set:
                logger.warning("Work report already in invalid set", wr_hash=wr_hash.hex())
                return

            state.invalid_set.append(wr_hash)
            self._tranche_store[tranche] = state
            logger.debug("Added work report to invalid set", wr_hash=wr_hash.hex())

tranche_store = TrancheStore()
