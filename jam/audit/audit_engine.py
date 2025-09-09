import asyncio
from time import process_time_ns

from tsrkit_types import Null, Option, TypedVector, Uint

from jam.audit.auditor import Auditor
from jam.audit.utils import Utils
from jam.block.extrinsics.disputes import DisputesExtrinsic, Verdicts, Culprits, Faults
from jam.block.block import Block
from jam.finality.finality import Finality
from jam.logging import get_logger
from jam.types import Hash

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

    async def run(self, block: Block, new_wrs: OptionalReports):
        print("111111111111111111111111111111111111111111111111111")
        print("current process header_hash", block.header.hash().hex())
        print("current process header_hash", block.header.hash())
        # print("NEWLY_WORK_REPORT ====================================================================>")
        # for i in new_wrs:
        #     print(i)
        from jam.settings import settings
        header_hash = block.header.hash()

        from jam.storage.tranche_audit_store import tranche_store
        from jam.state.state import State

        auditor = Auditor()
        audit = Utils()

        # -------------- Fetch Last Finalized Block --------------
        last_finalized_block = Finality.load_final(settings.main_db)

        if block.header.slot < last_finalized_block.header.slot:
            logger.info("Block must be finalized or invalid.")
            return

        # -------------- Fetch Pending Reports --------------
        logger.debug("Fetching prior state", ph=block.header.parent.hex())
        prior_state = State.load(block.header.parent)

        # -------------- Report to be Audited for this slot -----------

        # from jam.audit.dummy import build_rho
        # from jam.types.protocol.core import TimeSlot
        # rho = build_rho(time_out=TimeSlot(TimeSlot(1)))
        # print("RHO =========================================================================================")
        # for i in rho:
        #     print(i)

        # ============= dummy

        # unaudited_reports = audit.auditable_reports(prior_state=rho, newly_rep=new_wrs)
        # print("UNAUDITED_REPOT ========================================================================>", )
        # for i in unaudited_reports:
        #     print(Hash.blake2b((i.encode())))
        #     print(Hash.blake2b((i.encode())).hex())

        unaudited_reports = new_wrs
        # if block.header.author_index == settings.validator_index:
            # print("NEWLY_WORK_REPORT ====================================================================>")# print("================")
            # for i in unaudited_reports:
            #     print(i)
            #
            # print("HASH_REPO=========")
            # for i in unaudited_reports:
            #     print(Hash.blake2b(i.encode()))
            #
            # print("HEX_VALUE=========")
            # for i in unaudited_reports:
            #     print(Hash.blake2b(i.encode()).hex())


        # logger.debug("Fetched prior state", rho=prior_state, reps=unaudited_reports)

        # print("REPORT TO BE AUDIT", unaudited_reports)

        curr_ts = SLOT_PERIOD * int(block.header.slot)

        # Run Tranches continuously until block is audited
        while not self.is_audited:
            next_ts = curr_ts + AUDIT_PERIOD

            tranche_index = audit.tranche_index(header=block.header)
            curr_tranche = Tranche(tranche_index, header_hash)


            if tranche_index == TrancheIndex(0):

                if block.header.author_index == settings.validator_index:
                    tranche_state = TrancheState.empty()
                    tranche_state.unaudited_list = unaudited_reports
                    tranche_store.save_state(curr_tranche, tranche_state)

                else:
                    non_auth_state = tranche_store.get_state(tranche=curr_tranche)
                    non_auth_state.unaudited_list = unaudited_reports
                    tranche_store.save_state(curr_tranche, non_auth_state)

                no_shows = None

            else:
                # ------------------------------------- Handle > 0 Tranche Case -------------------------------------
                prev_tranche = Tranche(TrancheIndex(tranche_index - TrancheIndex(1)), header_hash)
                prev_state = tranche_store.get_state(tranche=prev_tranche)
                logger.debug(f"prev state {prev_tranche.tranche_index} = {settings.NODE_NAME} = {prev_state}")
                print("ho gya")
                # -------- CARRY FORWARD PREVIOUS STATE DATA AND SAVE STATE---------------
                print("current tranche index", curr_tranche.tranche_index)
                tranche_state = prev_state.carry_forward()

                tranche_store.save_state(tranche=curr_tranche, state=tranche_state)

                logger.debug(f"checking forward data {tranche_store.get_state(tranche=curr_tranche)}")

                no_shows, negative_wrs = await auditor.is_tranche(block=block, curr_tranche=curr_tranche, prev_state=prev_state)
                print("no_shows", no_shows, "tranche_index", tranche_index)
                print("negative_wrs", negative_wrs, "tranche_index", tranche_index)

                if len(negative_wrs) != 0:
                    await auditor.judgment_process(block=block, tranche=curr_tranche, negative_wrs=negative_wrs)

                # THIS IS THE CONDITION WHERE CHECK ALL CONDITION FOR "BLOCK AUDITED"
                if len(no_shows) == 0 and negative_wrs == 0:
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
                        from jam.block.extrinsics.disputes import dpt_store
                        dpt_store.store(d_ext)

                    else:
                        self.is_audited = True

                        logger.info(
                            f"Block Audited 🔍",
                            header_hash=header_hash.hex(),
                            block_slot=block.header.slot,
                            tranche=prev_tranche,
                        )
                    # not just audited condition
                    # Finality.finalise(header_hash, settings.main_db, False)
                    # tranche_store.remove_block_history(header_hash)
                    # return

                logger.info(
                    "New tranche started", header_hash=header_hash.hex(), tranche=tranche_index
                )

            try:
                print("timr left", next_ts - CURRENT_TIME())
                await asyncio.wait_for(
                    auditor.assignment_wrs(block, curr_tranche, no_shows), timeout=(next_ts - CURRENT_TIME())
                )

            except asyncio.TimeoutError:
                logger.warning("Audit timed out for block", block=str(block), tranche=curr_tranche)

            # Sleep for remainder time period
            await asyncio.sleep(next_ts - CURRENT_TIME())
            curr_ts += AUDIT_PERIOD
