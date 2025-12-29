import asyncio
from tsrkit_types import Null, Option, TypedVector, Uint
from jam.audit.auditor import Auditor
from jam.audit.audit import Audit
from jam.audit.utils import Utils
from jam.block.block import Block
from jam.finality.finality import Finality
from jam.log_setup import logger
from jam.network.protocols.ce_144 import SubsequentTrancheEvidence
from jam.types.audit.audit_tranche import (
    TrancheIndex,
    Tranche,
    TrancheState,
    OptionalReports,
)
from jam.types.work.report import WorkReports
from jam.utils.constants import AUDIT_PERIOD, CURRENT_TIME, SLOT_PERIOD
from jam.storage.tranche_audit_store import tranche_store
from jam.state.state import State
from jam.block.block_view import BlockView
from jam.settings import settings


class AuditEngine:
    """
    Audit engine initiates auditing and manages tranches for newly available reports.
    """

    def __init__(self):
        self.is_audited = False

    async def run(self, block: Block, newly_avail_wrs: WorkReports):
        header_hash = block.header.hash()

        auditor = Auditor()
        audit = Audit()
        utils = Utils()
        view = BlockView()

        logger.info("Auditing started", header_hash=header_hash.hex())

        # Fetch Last Finalized Block (defensive)
        last_finalized_block = Finality.load_final(kv=settings.main_db)
        if last_finalized_block is None:
            logger.error(
                "Finality.load_final returned None; aborting audit", header_hash=header_hash.hex()
            )
            return

        if block.header.slot < last_finalized_block.header.slot:
            logger.info(
                "Skipping audit because block slot is older than last finalized block",
                block_slot=int(block.header.slot),
                finalized_slot=int(last_finalized_block.header.slot),
            )
            return

        # Fetch Prior state
        logger.debug("Fetching prior state", ph=block.header.parent.hex())
        prior_state = State.load(header_hash=block.header.parent)
        if prior_state is None:
            logger.error(
                "State.load returned None; aborting audit", parent=block.header.parent.hex()
            )
            return

        # define q : TypedVector[Option[WorkReport]] = [ |R ?]
        auditable_reports: OptionalReports = audit.auditable_reports(
            prior_state=prior_state.rho, newly_rep=newly_avail_wrs
        )

        logger.debug(
            "Fetched prior state and auditable reports", rho=prior_state.rho, reps=auditable_reports
        )

        curr_ts = SLOT_PERIOD * int(block.header.slot)

        try:
            while not self.is_audited:
                next_ts = curr_ts + AUDIT_PERIOD
                tranche_index = audit.tranche_index(header=block.header)
                curr_tranche = Tranche(header_hash=header_hash, tranche_index=tranche_index)

                if tranche_index == TrancheIndex(0):
                    # ---------- BECAUSE BLOCK PRODUCED VALIDATOR TRIGGER FIRST ----------
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
                    # ------- Tranche > 0 ---------
                    logger.info(
                        "New tranche started",
                        header_hash=header_hash,
                        tranche=audit.tranche_index(header=block.header),
                    )
                    prev_tranche = Tranche(
                        TrancheIndex(tranche_index - TrancheIndex(1)), header_hash
                    )

                    prev_state = await tranche_store.get_state(tranche=prev_tranche)
                    if prev_state is None:
                        logger.error(
                            "prev_state is None; cannot continue tranche processing",
                            prev_tranche=prev_tranche,
                        )
                        break

                    tranche_state = await tranche_store.get_state(tranche=curr_tranche)
                    if tranche_state == TrancheState.empty():
                        tranche_state = prev_state.carry_forward()
                        await tranche_store.save_state(tranche=curr_tranche, state=tranche_state)

                    #  Condition which check trigger next tranche
                    subsequent_evidence: TypedVector[
                        SubsequentTrancheEvidence
                    ] = await utils.is_tranche(
                        block=block, curr_tranche=curr_tranche, prev_tranche_state=prev_state
                    )

                    if len(subsequent_evidence) == 0:
                        dispute_extrinsic = await utils.dispute_ext(
                            block=block, tranche=curr_tranche
                        )
                        logger.debug("Dispute extrinsic built", dispute_extrinsic=dispute_extrinsic)

                        is_block_audit = await utils.block_audited(
                            tranche=curr_tranche, block=block, newly_avail_wrs=newly_avail_wrs
                        )

                        if is_block_audit:
                            view.mark_as_audited(block=block, kv=settings.main_db)
                            self.is_audited = True
                            break

                        else:
                            logger.info(
                                "Block is not audited in this tranche",
                                tranche=curr_tranche,
                                header_hash=header_hash.hex(),
                            )

                try:
                    await asyncio.wait_for(
                        auditor.assignment_wrs(
                            block=block,
                            tranche=curr_tranche,
                            subsequent_evidence=subsequent_evidence,
                        ),
                        timeout=(next_ts - CURRENT_TIME()),
                    )

                except asyncio.TimeoutError:
                    logger.warning(
                        "Audit timed out for block", block=str(block), tranche=curr_tranche
                    )

                # Sleep for remainder time period
                await asyncio.sleep(next_ts - CURRENT_TIME())
                curr_ts += AUDIT_PERIOD

        except Exception:
            logger.exception("Unexpected exception in AuditEngine.run")
            raise
