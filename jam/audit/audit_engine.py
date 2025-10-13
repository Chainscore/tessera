import asyncio
from tsrkit_types import Null, Option, TypedVector, Uint
from jam.audit.auditor import Auditor
from jam.audit.audit import Audit
from jam.audit.utils import Utils
from jam.block.block import Block
from jam.finality.finality import Finality
from jam.log_setup import logger
from jam.network.protocols.ce_144 import SubsequentTrancheEvidence
from jam.types import Hash
from jam.types.audit.audit_tranche import (
    TrancheIndex,
    Tranche,
    TrancheState,
    OptionalReports,
)
from jam.types.work.report import WorkReports
from jam.utils.constants import AUDIT_PERIOD, CURRENT_TIME, SLOT_PERIOD


class AuditEngine:
    """
    Audit engine initiates auditing and manages tranches for newly available reports
    """

    is_audited: bool

    def __init__(self):
        self.is_audited = False

    async def run(self, block: Block, newly_avail_wrs: WorkReports):

        logger.info(f"Auditing started header_hash {block.header.hash()}")

        from jam.settings import settings
        header_hash = block.header.hash()

        from jam.storage.tranche_audit_store import tranche_store
        from jam.state.state import State

        auditor = Auditor()
        audit = Audit()
        utils = Utils

        # -------------- Fetch Last Finalized Block --------------
        last_finalized_block = Finality.load_final(settings.main_db)

        if block.header.slot < last_finalized_block.header.slot:
            logger.info("Block must be finalized or invalid.")
            return

        # -------------- Fetch Pending Reports --------------

        logger.debug("Fetching prior state", ph=block.header.parent.hex())
        prior_state = State.load(block.header.parent)

        # define q : TypedVector[Option[WorkReport]] = [ |R ?]
        auditable_reports : OptionalReports = audit.auditable_reports(prior_state=prior_state.rho, newly_rep=newly_avail_wrs)

        logger.debug("Fetched prior state", rho=prior_state.rho, reps=auditable_reports)


        curr_ts = SLOT_PERIOD * int(block.header.slot)

        while not self.is_audited:

            next_ts = curr_ts + AUDIT_PERIOD

            tranche_index = audit.tranche_index(header=block.header)

            curr_tranche = Tranche(
                header_hash=header_hash,
                tranche_index = tranche_index
            )

            if tranche_index == TrancheIndex(0):
                # ---------- BECAUSE BLOCK PRODUCED BLOCKED TRIGGER FIRST -----------------
                if block.header.author_index == settings.validator_index:
                    tranche_state = TrancheState.empty()
                    tranche_state.unaudited_list = auditable_reports
                    await tranche_store.save_state(curr_tranche, tranche_state)

                else:
                    non_auth_state = await tranche_store.get_state(tranche=curr_tranche)
                    non_auth_state.unaudited_list = auditable_reports
                    await tranche_store.save_state(curr_tranche, non_auth_state)

                subsequent_evidence = None

            else:
                # ------- Tranche > 0 handling ---------
                utils.print_banner(text="New Tranche Trigger | ", tranche_index=curr_tranche.tranche_index)
                logger.info(
                    "New tranche started", header_hash=header_hash, tranche=audit.tranche_index(header=block.header)
                )

                prev_tranche = Tranche(TrancheIndex(tranche_index - TrancheIndex(1)), header_hash)
                prev_state = await tranche_store.get_state(tranche=prev_tranche)


                tranche_state = await tranche_store.get_state(tranche=curr_tranche)

                if tranche_state == TrancheState.empty():
                    tranche_state = prev_state.carry_forward()
                    await tranche_store.save_state(tranche=curr_tranche, state=tranche_state)

                # ------------------- Condition which check trigger next tranche ---------------
                subsequent_evidence : TypedVector[SubsequentTrancheEvidence] = await utils.is_tranche(block=block, curr_tranche=curr_tranche, prev_tranche_state=prev_state)

                # if in this tranche subsequence is zero, means no report to audit for this tranche,
                # no announcements no judgments no further negative judgments
                if len(subsequent_evidence) == 0: # This say about new tranche follow or not due to no show

                    dispute_extrinsic = await utils.dispute_ext(block=block, tranche=curr_tranche)

                    is_block_audit = await utils.block_audited(tranche=curr_tranche, block=block, newly_avail_wrs=newly_avail_wrs)

                    if is_block_audit:
                        self.is_audited = True

                    else:
                        print("Not audited block")

                    # remove block tranche history after it become audited
                    await tranche_store.remove_block_history(header_hash=header_hash)

                    continue

            try:
                await asyncio.wait_for(
                    auditor.assignment_wrs(
                        block=block,
                        tranche=curr_tranche,
                        subsequent_evidence=subsequent_evidence
                    ),
                    timeout=(next_ts - CURRENT_TIME())
                )

            except asyncio.TimeoutError:
                logger.warning("Audit timed out for block", block=str(block), tranche=curr_tranche)

            # Sleep for remainder time period
            await asyncio.sleep(next_ts - CURRENT_TIME())
            curr_ts += AUDIT_PERIOD