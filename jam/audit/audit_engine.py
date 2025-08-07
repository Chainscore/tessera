import asyncio
from typing import List, Tuple
from tsrkit_types import Option, TypedVector, Null
from tsrkit_types.dictionary import Dictionary
from jam.block.block import Block
from jam.finality.finality import Finality
from jam.logging import get_logger
from jam.state.state import State
from jam.audit.utils import Utils
from jam.types.protocol.core import ValidatorIndex, CoreIndex
from jam.audit.auditor import Auditor
from jam.types.audit.tranche import TrancheIndex, Tranche, TrancheState, AuditRecord
from jam.types.protocol.crypto import HeaderHash
from jam.types.state.rho import WorkReportState
from jam.types.work.report import WorkReport, WorkReportHash, WorkReports
from jam.storage.tranche_store import tranche_store
from jam.utils.constants import AUDIT_PERIOD, CURRENT_TIME
from jam.network.protocols.ce_144 import Announcement


# Logger for Auditing module
logger = get_logger("audit")


class AuditEngine:
    """
    Audit engine initiates auditing and manages tranches for newly available reports
    """

    @classmethod
    async def run(cls, block: Block, new_wr: WorkReports, tranche_index: TrancheIndex):
        from jam.settings import settings

        from jam.network.start import node

        auditor = Auditor()
        utils = Utils()

        entropy = block.header.entropy_source

        # --------------------------------- Fetch Last Finalized Block -----------------------------------------
        last_finalized_block = Finality.load_final(settings.main_db)
        header_hash = block.header.hash()

        if block.header.slot < last_finalized_block.header.slot:
            logger.info("Block must be finalized or invalid.")
            return

        # ----------------------------- initialized state for node and saved ---------------------------------
        tranche_zero = Tranche(
            header_hash=header_hash,
            tranche_index=tranche_index
        )

        unaudited_list = List[Option[WorkReport]]([])
        announcements = Dictionary[ValidatorIndex, Announcement]({})
        valid_set = TypedVector[WorkReport]([])
        invalid_set = TypedVector[WorkReportHash]([])
        judgments = Dictionary[WorkReportHash, AuditRecord]({})

        tranche_state = TrancheState(
            unaudited_list=unaudited_list,
            announcements=announcements,
            judgments=judgments,
            valid_set=valid_set,
            invalid_set=invalid_set,
        )

        tranche_store.save_state(tranche=tranche_zero, tranche_state=tranche_state)

        # -------------------------- Fetch Pending Reports and calculate "q" and update state -------------------
        prior_state = State.load(block.header.parent)
        auditable_reports = List[Option[WorkReport]]([])

        for r in prior_state.rho:
            report_state: (WorkReportState | Null) = r.unwrap()
            if isinstance(report_state, WorkReportState) and r.report in new_wr:
                auditable_reports.append(Option[WorkReport](r.report))
            else:
                auditable_reports.append(Option[WorkReport](Null))

        tranche_store.add_to_unaudited(tranche=tranche_zero, unaudit_reports=auditable_reports)

        # -------------------------- Assigned report for TRANCHE = 0 -----------------------------------
        assigned_wr = List[Tuple[CoreIndex, WorkReport]]([])

        assigned_wr = utils.verifiable_random_selection(
            entropy_source=entropy,
            bandersnatch_key=node.b_key,
            unaudited_report=auditable_reports,
            tranche=tranche_zero
        )

        # ------------------ Start Announcement and Judgment for tranche = 0 and run for upto 8 seconds --------------------------

        await asyncio.wait_for(auditor.announce(tranche=tranche_zero, block=block, assigned_wrs=assigned_wr), timeout = AUDIT_PERIOD - (CURRENT_TIME - block.header.slot))  # block.header.slot this will update here


        # NEXT TRANCHE PROCESS START HERE FROM TRANCHE = 1
        tranche = cls.tranche_loop(tranche=TrancheIndex(1), block=block)


    @classmethod
    async def tranche_loop(cls, tranche: Tranche, block: Block):
        """
        """
        from jam.storage.da.reports import ReportsDA
        from jam.settings import settings

        utils = Utils()
        auditor =  Auditor()

        tranche_index = tranche.tranche_index
        header_hash = HeaderHash(block.header.hash())

        while True:

            # ---------------------- state initialize for TRANCHES > 0 --------------------------
            tranche = Tranche(
                header_hash=header_hash,
                tranche_index=tranche_index
            )

            unaudited_list = List[Option[WorkReport]]([])
            announcements = Dictionary[ValidatorIndex, Announcement]({})
            assigned_wrs = WorkReports([])
            records = Dictionary[WorkReportHash, AuditRecord]({})
            valid_set = TypedVector[WorkReport]([])
            invalid_set = TypedVector[WorkReportHash]([])

            tranche_state = TrancheState(
                unaudited_list=unaudited_list,
                announcements=announcements,
                assigned_wrs=assigned_wrs,
                records=records,
                valid_set=valid_set,
                invalid_set=invalid_set,
            )

            tranche_store.save_state(tranche=tranche, tranche_state=tranche_state)

            # CALCULATE NO-SHOWS TRANCHE > 0 and unaudited unaudited_report list in state
            no_shows = auditor.no_show_n_report(block=block, tranche=tranche)

            if len(no_shows) == 0:
                logger.info(f"Auditing for slot {block.header.slot} complete at Tranche {tranche_index}")
                return

            else:

                # ------------------------- GET NO_SHOW AND UPDATED Q -----------------------------------
                unaudited_list = tranche_store.get_unaudited_list(tranche=tranche)

                # ASSIGNED REPORTS FOR TRANCHE > 0
                assignment = utils.vrf_tranche(
                    header_hash=header_hash,
                    tranche=tranche,
                    entropy=entropy,
                    unaudited_wrs=unaudited_list
                )

                # time_left = currenttime() - tranche 1 start time

                # ASSIGNMENT REPORT FOR THIS REPORTS
                await asyncio.wait_for(auditor.announce(block=block, tranche=tranche, assigned_wrs=assignment, no_shows=no_shows), timeout=8 - (CURRENT_TIME - CURRENT_TIME ) )

                tranche_index =+ TrancheIndex(1)

"""
       TODO:
           - We receive a valid block (valid w.r.t state transition).
           - we check whether it is finalized or not.
           - if new, we start audit engine.

           - In first round (tranche):
               - we fetch initial q
               - then kickoff tranche 0

               ...

           - In subsequent tranche:
               - we have to find out unaudited list of reports.
               - we have to find all those validators who announced audit of that report but didn't send judgement for 
                that report
               - then from all those reports we have to find which reports to audit

           at the end of tranche / just at start of new tranche we have to check whether the report is audited or not.
           this must be done by checking that there must not be any unaudited report left. 
"""

# FETCH WORK-REPORT CORRESPONDING OF WORK-REPORT-HASH
# d3l = settings.d3l
# rep_da = ReportsDA(d3l)
# wr = rep_da.get(wr_hash=wr_hash)