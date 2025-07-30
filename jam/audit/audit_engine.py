import asyncio
from copy import deepcopy
from typing import List
from tsrkit_types import Option, TypedVector, Null
from tsrkit_types.dictionary import Dictionary

from jam.audit.auditor import Auditor
from jam.audit.tranche_engine import TrancheEngine
from jam.block.block import Block
from jam.finality.finality import Finality
from jam.logging import get_logger
from jam.state.state import State

from jam.types.audit.tranche import TrancheIndex, Tranche, TrancheState, AuditRecord
from jam.types.protocol.crypto import HeaderHash
from jam.types.state.rho import WorkReportState
from jam.types.work.report import WorkReport, WorkReportHash, WorkReports
from jam.storage.tranche_store import tranche_store, TrancheStore
from jam.utils.constants import CURRENT_TIME, SLOT_PERIOD, AUDIT_PERIOD, VALIDATOR_COUNT

# Logger for Auditing module
logger = get_logger("audit")


class AuditEngine:
    """
    Audit engine initiates auditing and manages tranches for newly available reports
    """

    @classmethod
    async def run(cls, block: Block, new_wr: WorkReports):
        from jam.network.node import node
        from jam.settings import settings

        header_hash = block.header.hash()

        auditor = Auditor()

        # -------------- Fetch Last Finalized Block --------------
        last_finalized_block = Finality.load_final(settings.main_db)
        header_hash = block.header.hash()

        if block.header.slot < last_finalized_block.header.slot:
            logger.info("Block must be finalized or invalid.")
            return

        # -------------- Fetch Pending Reports --------------
        prior_state = State.load(block.header.parent)
        auditable_reports = List[Option[WorkReport]]([])
        for r in prior_state.rho:
            report_state: (WorkReportState | Null) = r.unwrap()
            if isinstance(report_state, WorkReportState) and r.report in new_wr:
                auditable_reports.append(Option[WorkReport](r.report))
            else:
                auditable_reports.append(Option[WorkReport](Null))

        while True:
            tranche_index = TrancheIndex(
                (CURRENT_TIME() - (SLOT_PERIOD * int(block.header.slot))) // AUDIT_PERIOD
            )

            if tranche_index == TrancheIndex(0):
                tranche_state = TrancheState.empty()
                tranche_state.unaudited_list = TypedVector[Option[WorkReport]](auditable_reports)


            else:
                prev_tranche = Tranche(TrancheIndex(tranche_index - 1), header_hash)
                prev_state = tranche_store._get_state(prev_tranche)

                # Validation logic
                old_queue = prev_state.unaudited_list

                tranche_state = TrancheState.empty()
                tranche_state.judgment_map = prev_state.judgment_map
                tranche_state.valid_set = prev_state.valid_set
                tranche_state.invalid_set = prev_state.invalid_set

                # Audit check
                all_audited = True
                new_queue = old_queue
                for i, r in enumerate(old_queue):
                    rep = r.unwrap()
                    if isinstance(rep, WorkReport):
                        wr_hash = rep.hash()

                        # TODO: KeyError handling
                        judgment_map = tranche_state.judgment_map[wr_hash]
                        true_judgments = judgment_map.true_votes
                        false_judgments = judgment_map.false_votes

                        announcement_map = prev_state.announcement_map[wr_hash]

                        first_cond = len(false_judgments) == 0 and set(announcement_map).issubset(
                            set(true_judgments)
                        )
                        second_cond = len(true_judgments) > (2 * VALIDATOR_COUNT // 3)

                        if first_cond or second_cond:
                            new_queue[i] = Option[WorkReport](Null)
                            logger.debug(
                                "Report audited!",
                                header_hash=header_hash.hex(),
                                tranche=tranche_index - 1,
                                wr_hash=wr_hash.hex(),
                            )
                        elif len(false_judgments) >= VALIDATOR_COUNT * 1 // 3:
                            # TODO: Block will be ban-listed
                            tranche_state.invalid_set.append(r)
                            all_audited = False
                            logger.debug(
                                "Report invalid!",
                                header_hash=header_hash.hex(),
                                tranche=tranche_index,
                                wr_hash=wr_hash.hex(),
                            )
                        else:
                            logger.debug(
                                "Report moving to next tranche!",
                                header_hash=header_hash.hex(),
                                tranche=tranche_index,
                                wr_hash=wr_hash.hex(),
                            )
                            all_audited = False

                if all_audited:
                    logger.info(
                        "Block audited successfully!",
                        header_hash=header_hash.hex(),
                        tranche=tranche_index - 1,
                    )
                    return

                tranche_state.unaudited_list = new_queue

                logger.info(
                    "New tranche started", header_hash=header_hash.hex(), tranche=tranche_index
                )

            # Do mapping stuff
            curr_tranche = Tranche(tranche_index, header_hash)
            tranche_store._save_state(curr_tranche, tranche_state)
            asyncio.create_task(auditor.audit(block, tranche_index))

            # Check for noshows at the end
            break

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
