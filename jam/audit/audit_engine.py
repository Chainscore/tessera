import asyncio

from tsrkit_types import Null

from jam.audit.auditor import Auditor
from jam.block.block import Block
from jam.finality.finality import Finality
from jam.log_setup import node_logger as logger
from jam.network.protocols.ce_144 import NoShows

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

        if len(new_wr) == 0:
            logger.info("No New Reports to audit, finalizing block!", block=str(block))
            Finality.finalise(header_hash, settings.main_db, False)
            return

        from jam.storage.tranche_store import tranche_store
        from jam.state.state import State, state

        auditor = Auditor()

        entropy = block.header.entropy_source

        # -------------- Fetch Last Finalized Block --------------
        last_finalized_block = Finality.load_final(settings.main_db)

        logger.info(
            "Block Auditing started 🔍🪛",
            block=str(block),
            reports=new_wr
        )
        if block.header.slot < last_finalized_block.header.slot:
            logger.info("Block must be finalized or invalid.")
            return

        # -------------- Fetch Pending Reports --------------
        prior_state = State.load(block.header.parent)
        auditable_reports = OptionalReports([])
        for r in prior_state.rho:
            report_state: (WorkReportState | Null) = r.unwrap()
            if isinstance(report_state, WorkReportState) and report_state.report in new_wr:
                auditable_reports.append(OptionalReport(report_state.report))
            else:
                auditable_reports.append(OptionalReport(Null))

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
                await tranche_store.save_state(curr_tranche, tranche_state)
                no_shows = None

            else:
                # Handle > 0 Tranche Case
                prev_tranche = Tranche(TrancheIndex(tranche_index - 1), header_hash)
                prev_state = await tranche_store.get_state(prev_tranche)

                tranche_state = prev_state.carry_forward()
                await tranche_store.save_state(curr_tranche, tranche_state)

                # Audit check
                no_shows: NoShows = await auditor.is_audited(block, curr_tranche)

                if len(no_shows) == 0:
                    self.is_audited = True
                    logger.info(
                        f"Block Audited 🔍",
                        header_hash=header_hash.hex(),
                        block_slot=block.header.slot,
                        tranche=prev_tranche,
                    )
                    Finality.finalise(header_hash, settings.main_db, False)
                    tranche_store.remove_block_history(header_hash)
                    return

                logger.info(
                    "New tranche started", header_hash=header_hash.hex(), tranche=tranche_index
                )

            # Trigger auditing
            try:
                await asyncio.wait_for(
                    auditor.audit(block, curr_tranche, no_shows), timeout=(next_ts - CURRENT_TIME())
                )
            except asyncio.TimeoutError:
                logger.warning("Audit timed out for block", block=str(block), tranche=curr_tranche)

            # Sleep for remainder time period
            await asyncio.sleep(next_ts - CURRENT_TIME())
            curr_ts += AUDIT_PERIOD
