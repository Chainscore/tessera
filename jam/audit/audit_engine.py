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
from jam.audit.utils import Utils
from jam.types.protocol.core import ValidatorIndex


from jam.types.audit.tranche import TrancheIndex, Tranche, TrancheState, AuditRecord
from jam.types.protocol.crypto import HeaderHash
from jam.types.state.rho import WorkReportState
from jam.types.work.report import WorkReport, WorkReportHash, WorkReports
from jam.storage.tranche_store import tranche_store, TrancheStore
from jam.utils.constants import CURRENT_TIME, SLOT_PERIOD, AUDIT_PERIOD, VALIDATOR_COUNT
from jam.network.protocols.ce_144 import Announcement, NoShow


# Logger for Auditing module
logger = get_logger("audit")


class AuditEngine:
    """
    Audit engine initiates auditing and manages tranches for newly available reports
    """

    @classmethod
    async def run(cls, block: Block, new_wr: WorkReports):
        from jam.settings import settings

        auditor = Auditor()
        utils = Utils()

        # -------------- Fetch Last Finalized Block --------------
        last_finalized_block = Finality.load_final(settings.main_db)
        header_hash = block.header.hash()

        if block.header.slot < last_finalized_block.header.slot:
            logger.info("Block must be finalized or invalid.")
            return

        # ------------- Initialize tranche and processed --------------
        tranche_index = TrancheIndex(0)

        # ----------------------------- initialized state for node and saved -----------------------
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

        # -------------- Fetch Pending Reports --------------
        prior_state = State.load(block.header.parent)
        auditable_reports = List[Option[WorkReport]]([])

        for r in prior_state.rho:
            report_state: (WorkReportState | Null) = r.unwrap()
            if isinstance(report_state, WorkReportState) and r.report in new_wr:
                auditable_reports.append(Option[WorkReport](r.report))
            else:
                auditable_reports.append(Option[WorkReport](Null))

        tranche_store.add_to_unaudited(tranche=tranche_zero, unaudit_reports=auditable_reports)

        while True:
            tranche_index = utils.tranche_index(block=block)

            if tranche_index == TrancheIndex(0):
                tranche_state = TrancheState.empty()
                tranche_state.unaudited_list = TypedVector[Option[WorkReport]](auditable_reports)

            else:
                prev_tranche = Tranche(TrancheIndex(tranche_index - 1), header_hash)
                prev_state = tranche_store.get_state(prev_tranche)

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

    @classmethod
    def assigned_report(cls, block: Block, tranche: Tranche):
        from jam.network.node import node

        audit = Utils()

        assigned_wr = List[WorkReport]([])

        tranche_index = tranche.tranche_index
        header_hash = tranche.header_hash
        tranche_state = tranche_store.get_state(tranche)
        reports_queue = tranche_state.unaudited_list

        entropy = block.header.entropy_source

        if tranche_index == 0:

            assigned_wr = audit.verifiable_random_selection(
                entropy_source=entropy,
                bandersnatch_key=node.b_key,
                unaudited_report=reports_queue,
                tranche=tranche
            )

            return assigned_wr

        else:

            pre_tranche=Tranche(
                header_hash=header_hash,
                tranche_index=tranche_index - TrancheIndex(1)
            )

            state = tranche_store.get_state(tranche=pre_tranche)
            records = state.records

            no_show = TypedVector[NoShow]([])

            for wr_hash, record in records.items():
                announce = len(record.announces)
                true = len(record.true_votes)
                false = len(record.false_votes)
                no_votes = len(record.no_votes)

                if announce > true + false and no_votes != 0:
                    for v in AuditRecord.no_votes:
                        ann_list = tranche_store.get_set_announcement(
                            tranche=Tranche(
                                header_hash=header_hash,
                                tranche_index=tranche_index - TrancheIndex(1)
                            ),
                            validator_index=v
                        )
                        if v not in [k for k, _ in no_show]:
                            no_show.append(NoShow(
                                validator_index=v,
                                announcement=ann_list)
                            )
                        else:
                            logger.info("Validator announcement already exists")

                    while len(no_show) != 0:
                        tranche = Tranche(
                            header_hash=header_hash,
                            tranche_index=tranche_index
                        )

            assigned_wr = audit.vrf_tranche(
                header_hash=tranche.header_hash,
                no_shows=no_show,
                tranche=tranche,
                entropy=entropy
            )

            return assigned_wr