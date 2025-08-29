from typing import Dict, Tuple

from pycparser.ply.ctokens import t_RSHIFT
from tsrkit_types import Bool, Option, TypedVector
import bisect

from jam.logging import get_logger
from jam.network.protocols.ce_144 import Announcement

from jam.types.audit.tranche import Tranche, TrancheState, AuditRecord, OptionalReports, ValidatorSignature
from jam.network.protocols.ce_144 import NoShow
from jam.types.protocol.core import ValidatorIndex, CoreIndex
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

    def get_state(self, tranche: Tranche) -> TrancheState:
        """ Retrieve a TrancheState by Tranche object. """
        try:
            state = self._tranche_store.get(tranche)
            if state:
                return state
            else:
                logger.error(f"Error while retrieved tranche store for tranche: {tranche} ")
                return TrancheState.empty()

        except Exception as e:
            logger.error(f"Error in 'get_state' function while retrieved state through tranche {e}")


    def save_state(self, tranche: Tranche, state: TrancheState):
        """ Store TrancheState under its tranche key automatically."""
        self._tranche_store[tranche] = state


    # --------------------- Tranche Operations --------------------

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


    # --------------------- WR Queue Access Operations ------------
    def update_unaudited_list(self, tranche: Tranche, unaudited_reports: OptionalReports):
        # TODO: function name changed also change in "Test Vectors"
        """ ####################################### """
        try:
            state = self.get_state(tranche)
            if state:
                state.unaudited_list = unaudited_reports
                self.save_state(tranche=tranche, state=state)
                logger.info(f"Build and updated unaudited list for the tranches {tranche}")
            else:
                logger.info(f"Updated unaudited list for the tranches {tranche}")

        except Exception as e:
            logger.exception(f"Error while retrieving unaudited list for tranche {tranche}: {e}")


    # def get_unaudited_list(self, tranche: Tranche):  eski need nhi h kyuki hne direct he
    #     """ ##################################### """
    #     try:
    #         state = self._tranche_store.get(tranche)
    #         if state:
    #             return state.unaudited_list
    #         else:
    #             logger.error(f"'unaudited_list' not found in state for tranche: {tranche}")
    #     except Exception as e:
    #         logger.exception(f"Error while retrieving unaudited list for tranche {tranche}: {e}")

    def rm_from_unaudited(self, tranche: Tranche, wr_hash: WorkReportHash):
        """ ###################################### """
        try:
            state = self.get_state(tranche)
            if state:
                state.unaudited_list.remove(wr_hash)
                self.save_state(tranche, state)
                logger.info(f"Successfully removed work report from unaudited list", wr_hash=wr_hash.hex())

            else:
                logger.error(f"'unaudited_list' not found in state for tranche: {tranche}")

        except Exception as e:
            logger.exception(f"Error while retrieving unaudited list for tranche {tranche}: {e}")

    # def add_to_audited(self, tranche: Tranche, wr_hash: WorkReportHash):
    #     """ ################################################ """
    #     try:
    #         state = self._tranche_store.get(tranche)
    #         if state:
    #             state.audited_list.append(wr_hash)
    #         else:
    #             logger.error(f"'unaudited_list' not found in state for tranche: {tranche}")
    #
    #     except Exception as e:
    #         logger.error(f"Error while adding Work Report hash to Audited list for tranche {tranche}: {e}")


    # --------------------- Announcement Operations ---------------------
    # wr -> announce
    def records_announcement(self, tranche: Tranche, validator_index: ValidatorIndex, announce: Announcement):
        """ Here add no_shows and validator_index in announcement """
        from jam.settings import settings

        state = self.get_state(tranche=tranche)

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

        self.save_state(tranche, state)



    # def record_announcement(self, tranche: Tranche, validator_index: ValidatorIndex, ann: Announcement):
    #
    #     from jam.settings import settings
    #
    #     state = self.get_state(tranche)
    #
    #     print(settings.NODE_NAME, "Tranche State Fetched", state.records.to_json(), "\n\n")
    #
    #
    #     # if validator_index not in state.announcements:
    #     #     state.announcements[validator_index] = ann
    #
    #     for rep in ann.assigned_reports:
    #         wr_hash = rep.report_hash
    #         if wr_hash not in state.records:
    #             state.records[wr_hash] = AuditRecord.empty()
    #
    #         if validator_index not in state.records[wr_hash].announces:
    #             state.records[wr_hash].announces.append(validator_index)
    #
    #         if validator_index not in state.records[wr_hash].no_votes:
    #             no_show = NoShow(
    #                 validator_index= validator_index,
    #                 announcement= ann
    #             )
    #
    #             state.records[wr_hash].no_votes.append(no_show)
    #
    #     self.save_state(tranche, state)
    #     print(settings.NODE_NAME, "Tranche State Saved", state.records.to_json(), "\n\n")
    #     logger.info("Recorded audit announcement", tranche=tranche, vi=validator_index, ann=ann)


    # --------------------- Judgement Operations ---------------------

    def update_judgment(self,
        tranche: Tranche,
        validator_index: ValidatorIndex,
        judgment: Bool,
        wr_hash: WorkReportHash,
        edd2519_signature: Ed25519Signature,
        ed25519_public: Ed25519Public
        ):
        """ ... """
        from jam.settings import settings
        state = self.get_state(tranche)

        if wr_hash not in state.records:
            logger.debug("Unknown Report Judgement received", validator=validator_index)
            return

        logger.debug("")
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

        self.save_state(tranche, state)
        logger.debug("Updated judgment for work report", wr_hash=wr_hash.hex())

    def get_judgment(self, tranche: Tranche, wr_hash: WorkReportHash) -> AuditRecord | None:   # no use for more
        state = self.get_state(tranche)
        return state.records.get(wr_hash)


    # --------------------- Validity Operations ---------------------
    def add_to_valid_set(self, tranche: Tranche, c_w: Tuple[CoreIndex, WorkReportHash]):
        state = self.get_state(tranche)
        if c_w in state.valid_set:
            logger.warning("Work report already in valid set", c_w=c_w[1].hex())
            return

        state.valid_set.append(c_w)
        self.save_state(tranche, state)
        logger.debug("Added work report to valid set", c_w=c_w[1].hex())

    def add_to_invalid_set(self, tranche: Tranche, c_w: Tuple[CoreIndex, WorkReportHash]):
        state = self.get_state(tranche)
        if c_w in state.invalid_set:
            logger.warning("Work report already in invalid set", c_w=c_w[1].hex())
            return
        state.invalid_set.append(c_w)
        self.save_state(tranche, state)
        logger.debug("Added work report to invalid set", c_w=c_w[1].hex())

    def add_to_wonky_set(self, tranche: Tranche, c_w: Tuple[CoreIndex, WorkReportHash]):
        state = self.get_state(tranche)
        if c_w in state.wonky_set:
            logger.warning("Work report already in wonky set", c_w=c_w[1].hex())
            return
        state.wonky_set.append(c_w)
        self.save_state(tranche, state)
        logger.debug("Added work report to wonky set", c_w=c_w[1].hex())


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
