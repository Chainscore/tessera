import asyncio

from sympy.physics.units import current
from tsrkit_types import TypedVector, Option

from jam.audit.audit_process import AuditProcess
from jam.audit.q import sample_work_reports_with_nulls
from jam.block.extrinsics.disputes import Culprits, Faults, Verdicts
from jam.network.protocols.ce_144 import NoShow
from jam.utils.constants import AUDIT_PERIOD
from jam.types.protocol.core import TrancheIndex
from jam.types.protocol.crypto import  HeaderHash
from jam.logging import get_logger
from tsrkit_types.dictionary import Dictionary

from jam.operations.tranche_store import Tranche, TrancheState, JudgmentRecord, TrancheStore,tranche_store
from jam.types.work.report import WorkReport, WorkReportHash
from jam.audit.audit import AuditingAndJudgement
from jam.finality.finality import Finality
from jam.utils.constants import CORE_COUNT


logger = get_logger("tranche_engine")


class TrancheEngine:
    def __init__(self):
        self.store = tranche_store
        self.audit_process = AuditProcess()
        self.audit = AuditingAndJudgement()

    async def run(self, header_hash: HeaderHash, newly_avail_wrs: list[Option[WorkReport]]):
        from jam.network.node import node

        # ----------------------------- check node in initialized or not ---------------------------
        if not node.is_initialized:
            logger.debug("Network not initialized – skipping audit")
            return

        # -------------------------- Initialize tranche and processed ------------------------------
        tranche_index = TrancheIndex(0)

        # ----------------------------- initialized state for node and saved -----------------------
        init_tranche = Tranche(
            header_hash=header_hash,
            tranche_index=tranche_index
        )

        unaudited_list = list[Option[WorkReport]]
        valid_set = TypedVector[WorkReport]([])
        invalid_set = TypedVector[WorkReportHash]([])
        judgments = Dictionary[WorkReportHash, JudgmentRecord]({})

        tranche_state=TrancheState(
            unaudited_list=unaudited_list,
            judgments=judgments,
            valid_set=valid_set,
            invalid_set=invalid_set,
        )

        tranche_store._save_state(tranche=init_tranche, tranche_state=tranche_state)

        # ------------------------- Core auditing process started here ----------------------------

        # STATE - 1 => HERE WE GET EMPTY STATE FOR tranche 0
        present_state = self.store.get_state(tranche=Tranche(tranche_index=tranche_index, header_hash=header_hash))
        print(present_state)

        from jam.audit.audit import AuditingAndJudgement
        # from jam.state.state import state
        from jam.settings import settings
        from jam.network.node import node

        audit = AuditingAndJudgement()

        # ---------------------- Rho initial state ( pending wor reports) -------------------------
        logger.info(f"Current Block header hash")
        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()
        parent_hash = latest_block.header.parent

        logger.info(f"Get rho pending state here")
        # pending_rho_ = state.load(header_hash=parent_hash).rho

        # ---------------------- Block's header entropy sources -----------------------------------
        entropy = latest_block.header.entropy_source

        final_list = sample_work_reports_with_nulls("jam/combine.json", total_items=12, null_count=4)

        try:

            # pre audit reports
            logger.info(f"Get reports list which about to be audit")

            # ------------------------------- calculated q = [W?] --------------------------------
            unaudited_report = audit.report_to_be_audit(
                pending_wrs=final_list,
                newly_avail_wrs=newly_avail_wrs
            )

            tranche_store.add_to_unaudited(tranche=init_tranche, unaudit_reports=unaudited_report)

            # assignment report for auditing to validators
            logger.info(f"Work report assignment for auditing")

            reports = audit.verifiable_random_selection(entropy_source=entropy, bandersnatch_key=node.b_key,
                                                        unaudited_report=unaudited_report, tranche=init_tranche)

            logger.info(
                f"Checking assign report length {len(reports)} for each validator"
            )

            await asyncio.wait_for(
                asyncio.shield(self.audit_process.announce_judgment(assign_wrs=reports, tranche=init_tranche)),
                timeout=8)

            tranche_index += TrancheIndex(1)

            # STATE AFTER 0 TRANCHE, AT 8 SECONDS
            zero_tranche = self.store.get_state(
                tranche=Tranche(
                    tranche_index=tranche_index,
                    header_hash=header_hash
                )
            )

            judgments = zero_tranche.judgments




        except Exception as e:
            logger.error(
                "Failed to report assignment and judgment",
                error=str(e),
                err_type=type(e).__name__,
                exc_info=True,
            )
            raise

        else:
            while len(no_show) != 0:

                from jam.settings import settings

                tranche_index += TrancheIndex(1)
                no_show = self.tranche_loop(tranche= tranche, no_show=no_show)
                if len(no_show) == 0:
                    break

            await asyncio.sleep(AUDIT_PERIOD)


    def tranche_loop(self, tranche: Tranche, no_show: TypedVector[NoShow] ):
        if tranche.tranche_index > 0:
            no_shows = list[NoShow]([])

            # get entropy based on header hash
            latest_block = Finality.load_latest(kv=settings.main_db)
            entropy = latest_block.header.entropy_source

            assignment: list[WorkReport] = self.audit.vrf_tranche(header_hash=header_hash, no_shows=no_shows,
                                                                  tranche_index=tranche_index, entropy=entropy)

            # here we map them according to what audit accouncemet takes

            announcment = self.audit_process.audit_announcement(assign_wrs=assignment, tranche_index=tranche_index)

            noshow = self.audit_process.judgment_process(assign_wrs=assignment, tranche_index=tranche_index)

            return noshow




