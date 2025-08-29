import asyncio

from tsrkit_types import Null

from jam.audit.auditor import Auditor
from jam.block.extrinsics.disputes import DisputesExtrinsic, Verdicts, Culprits, Faults
from jam.block.block import Block
from jam.finality.finality import Finality
from jam.logging import get_logger

from jam.types.audit.tranche import (
    TrancheIndex,
    Tranche,
    TrancheState,
    OptionalReports,
    OptionalReport,
)
from jam.types.state.rho import WorkReportState
from jam.types.work.report import WorkReports
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

    async def run(self, block: Block, new_wr: WorkReports):
        from jam.settings import settings
        header_hash = block.header.hash()

        from jam.storage.tranche_store import tranche_store
        from jam.state.state import State, state

        auditor = Auditor()

        # -------------- Fetch Last Finalized Block --------------
        last_finalized_block = Finality.load_final(settings.main_db)

        if block.header.slot < last_finalized_block.header.slot:
            logger.info("Block must be finalized or invalid.")
            return

        # -------------- Fetch Pending Reports --------------
        logger.debug("Fetching prior state", ph=block.header.parent.hex())
        prior_state = State.load(block.header.parent)
        auditable_reports = OptionalReports([])

        print("PRIOR STATE", settings.NODE_NAME, block.header.parent.hex(),  prior_state.root.hex(), prior_state.rho.to_json(), header_hash.hex(), state.root.hex(), state.rho.to_json())

        for r in prior_state.rho:
            report_state: (WorkReportState | Null) = r.unwrap()
            if isinstance(report_state, WorkReportState) and report_state.report in new_wr:
                auditable_reports.append(OptionalReport(report_state.report))
            else:
                auditable_reports.append(OptionalReport(Null))

        logger.debug("Fetched prior state", rho=prior_state.rho.to_json(), reps=auditable_reports.to_json())

        curr_ts = SLOT_PERIOD * int(block.header.slot)

        # Run Tranches continuously until block is audited
        while not self.is_audited:
            next_ts = curr_ts + AUDIT_PERIOD

            tranche_index = TrancheIndex(
                (CURRENT_TIME() - (SLOT_PERIOD * int(block.header.slot))) // AUDIT_PERIOD
            )

            curr_tranche = Tranche(tranche_index, header_hash)
            if tranche_index == TrancheIndex(0):
                # Handle 0 Tranche Case
                tranche_state = TrancheState.empty()
                tranche_state.unaudited_list = auditable_reports
                tranche_store.save_state(curr_tranche, tranche_state)

                no_shows = None

            else:
                # ------------------------------------- Handle > 0 Tranche Case -------------------------------------
                prev_tranche = Tranche(TrancheIndex(tranche_index - TrancheIndex(1)), header_hash)
                prev_state = tranche_store.get_state(tranche=prev_tranche)

                # -------- CARRY FORWARD PREVIOUS STATE DATA AND SAVE STATE---------------
                tranche_state = prev_state.carry_forward()
                tranche_store.save_state(tranche=curr_tranche, state=tranche_state)

                no_shows, negative_wrs = auditor.is_tranche(block=block, curr_tranche=curr_tranche, prev_state=prev_state)

                if len(negative_wrs) != 0:
                    await auditor.judgment_process(block=block, tranche=curr_tranche, negative_wrs=negative_wrs)

                # THIS IS THE CONDITION WHERE CHECK ALL CONDITION FOR "BLOCK AUDITED"
                if len(no_shows) == 0 and negative_wrs == 0:
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
                    from jam.block.extrinsics.disputes import dpt_store
                    dpt_store.store(d_ext)

                    self.is_audited = True

                    logger.info(
                        f"Block Audited 🔍",
                        header_hash=header_hash.hex(),
                        block_slot=block.header.slot,
                        tranche=prev_tranche,
                    )
                    # not just audited condition
                    Finality.finalise(header_hash, settings.main_db, False)
                    return

                logger.info(
                    "New tranche started", header_hash=header_hash.hex(), tranche=tranche_index
                )

            try:
                await asyncio.wait_for(
                    auditor.assignment_wrs(block, curr_tranche, no_shows, ), timeout=(next_ts - CURRENT_TIME())
                )

            except asyncio.TimeoutError:
                logger.warning("Audit timed out for block", block=str(block), tranche=curr_tranche)

            # Sleep for remainder time period
            await asyncio.sleep(next_ts - CURRENT_TIME())
            curr_ts += AUDIT_PERIOD
