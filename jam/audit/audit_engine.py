import asyncio
from tsrkit_types import Null, Option, TypedVector, Uint

from jam.audit.auditor import Auditor
from jam.audit.audit import Audit
from jam.block.extrinsics.disputes import DisputesExtrinsic, Verdicts, Culprits, Faults
from jam.block.block import Block
from jam.finality.finality import Finality
from jam.logging import get_logger
from jam.types import Hash, TimeSlot

from jam.types.audit.audit_tranche import (
    TrancheIndex,
    Tranche,
    TrancheState,
    OptionalReports,
    OptionalReport,
)
from jam.types.state.rho import WorkReportState
from jam.types.work.report import WorkReports, WorkReport
from jam.utils.constants import AUDIT_PERIOD, CURRENT_TIME, SLOT_PERIOD

# Logger for Auditing module
logger = get_logger("auditor")


class AuditEngine:
    """
    Audit engine initiates auditing and manages tranches for newly available reports
    """

    is_audited: bool

    def __init__(self):
        self.is_audited = False

    async def run(self, block: Block, new_wrs: WorkReports):

        logger.info(f"Auditing process started for header_hash {block.header.hash()}")

        from jam.settings import settings
        header_hash = block.header.hash()

        from jam.storage.tranche_audit_store import tranche_store
        from jam.state.state import State

        auditor = Auditor()
        audit = Audit()

        # -------------- Fetch Last Finalized Block --------------
        last_finalized_block = Finality.load_final(settings.main_db)

        if block.header.slot < last_finalized_block.header.slot:
            logger.info("Block must be finalized or invalid.")
            return

        # -------------- Fetch Pending Reports --------------
        """
        logger.debug("Fetching prior state", ph=block.header.parent.hex())
        prior_state = State.load(block.header.parent)
        auditable_reports = OptionalReports([])

        # define q : TypedVector[Option[WorkReport]] = [ |R ?]
        auditable_reports = audit.auditable_reports(prior_state=prior_state.rho, newly_rep=new_wrs)
        
        logger.debug("Fetched prior state", rho=prior_state.rho, reps=auditable_reports)
        """

        # dummy ========================================================================================================
        from jam.audit.dummy import sample_work_reports_with_nulls

        auditable_reports = sample_work_reports_with_nulls(
            filepath="/home/dikshant441/Desktop/jam/tessera/jam/combined.json", total_items=4, null_count=0)
        # dummy ========================================================================================================

        curr_ts = SLOT_PERIOD * int(block.header.slot)

        # Run Tranches continuously until block is audited
        while not self.is_audited:

            next_ts = curr_ts + AUDIT_PERIOD

            # get tranche index
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
                    tranche_store.save_state(curr_tranche, tranche_state)

                else:
                    non_auth_state = tranche_store.get_state(tranche=curr_tranche)
                    non_auth_state.unaudited_list = auditable_reports
                    tranche_store.save_state(curr_tranche, non_auth_state)

                subsequent_evidence = None

            else:
                # ------------------------------------- Handle > 0 Tranche Case --------------------
                logger.info(
                    "New tranche started", header_hash=header_hash, tranche=audit.tranche_index(header=block.header)
                )

                prev_tranche = Tranche(TrancheIndex(tranche_index - TrancheIndex(1)), header_hash)
                prev_state = tranche_store.get_state(tranche=prev_tranche)

                tranche_state = prev_state.carry_forward()
                tranche_store.save_state(tranche=curr_tranche, state=tranche_state)

                # ------------------- Condition which check trigger next tranche ---------------
                subsequent_evidence = await auditor.is_tranche(block=block, curr_tranche=curr_tranche, prev_tranche_state=prev_state)

                # THIS IS THE CONDITION WHERE CHECK ALL CONDITION FOR "BLOCK AUDITED"
                if len(subsequent_evidence) == 0:
                    if tranche_index > TrancheIndex(1):
                        # 1. build dispute extrinsic
                        final_tranche_state = tranche_store.get_state(tranche=curr_tranche)

                        # verdict condition check
                        verdicts = final_tranche_state.dispute.verdicts
                        culprits = final_tranche_state.dispute.culprits
                        faults = final_tranche_state.dispute.faults

                        # sorted on based on work report_hash
                        sorted_verdicts = sorted(verdicts, key=lambda x: int.from_bytes(x[0]))

                        # sorted on based on work report_hash
                        sorted_culprits = sorted(culprits, key=lambda x: int.from_bytes(x[1]))

                        # sorted on based on work report_hash
                        sorted_faults = sorted(faults, key=lambda x: int.from_bytes(x[1]))

                        # Collect dispute in sorted order
                        d_ext = DisputesExtrinsic(
                            verdicts= Verdicts(sorted_verdicts),
                            culprits= Culprits(sorted_culprits),
                            faults= Faults(sorted_faults)
                        )

                        # add dispute extrinsic
                        # from jam.block.extrinsics.disputes import dpt_store
                        # dpt_store.store(d_ext)

                    self.is_audited = True

                    await tranche_store.remove_block_history(header_hash=header_hash)

                    logger.info(
                        f"Block Audited 🔍 from audit engine",
                        header_hash=header_hash.hex(),
                        block_slot=block.header.slot,
                        tranche=prev_tranche,
                    )

                    audit.block_audited(tranche=curr_tranche , block=block)

                    continue

            try:
                print("timr left", next_ts - CURRENT_TIME())
                await asyncio.wait_for(
                    auditor.assignment_wrs(block, curr_tranche, subsequent_evidence), timeout=(next_ts - CURRENT_TIME())
                )

            except asyncio.TimeoutError:
                logger.warning("Audit timed out for block", block=str(block), tranche=curr_tranche)

            # Sleep for remainder time period
            await asyncio.sleep(next_ts - CURRENT_TIME())
            curr_ts += AUDIT_PERIOD
