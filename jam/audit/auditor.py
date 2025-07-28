import asyncio
import math
from typing import List, Tuple, cast

from tsrkit_types import structure, U8, U32, TypedVector, Option, Null

from jam.block import Block
from jam.types import Hash, BandersnatchVrfSignature, ValidatorIndex, Ed25519Signature
from jam.types.protocol.core import CoreIndex, EpochIndex

from jam.finality.finality import Finality
from jam.audit.q import sample_work_reports_with_nulls, get_work_package_by_rep_hash
from jam.state.state import State
from jam.types import OptionalWorkReportState

from jam.types.audit.tranche import TrancheIndex
from jam.types.protocol.core import CoreIndex, EpochIndex
from jam.types.protocol.crypto import Hash, BandersnatchVrfSignature
from jam.types.state.rho import WorkReportState
from jam.types.work.report import WorkReport, WorkReportHash

from jam.logging import get_logger
from jam.utils.constants import EPOCH_LENGTH


# Module-specifier logger
logger = get_logger("auditor")

@structure
class Auditor:
    @classmethod
    async def audit(cls, block: Block, newly_avail_wrs: List[Option[WorkReport]], tranche_idx: TrancheIndex = TrancheIndex(0)):
        from jam.audit.audit import Utils

        # from jam.state.state import state
        from jam.settings import settings
        from jam.network.node import node
        from jam.operations.tranche_store import tranche_store, Tranche


        audit = Utils()

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
            if isinstance(report_state, WorkReportState) and r.report in newly_avail_wrs:
                auditable_reports.append(Option(r.report))
            else:
                auditable_reports.append(Option(Null))

        entropy = block.header.entropy_source

        try:
            # Pre Audit Reports
            logger.info(f"Fetching auditable reports per core")

            # TODO: Remove this
            # auditable_reports = audit.fetch_auditable_reports(prior_state, block)

            # ---------------------- Update the q in tranche store ------------------------------------
            tranche = Tranche(
                tranche_index=tranche_idx,
                header_hash=header_hash
            )

            tranche_store.add_to_unaudited(tranche=tranche, p_a_r=auditable_reports)

            # assignment report for auditing to validators
            logger.info(f"Work report assignment for auditing")

            reports = audit.verifiable_random_selection(entropy_source=entropy, bandersnatch_key=node.b_key, pre_audit_report=auditable_reports)

            logger.info(
                f"Checking assign report length {len(reports)} for each validator"
            )

            asyncio.create_task(cls.audit_announcement(assign_wrs=reports, tranche_idx=tranche_idx))
            asyncio.create_task(cls.judgment_process(assign_wrs=reports, tranche_idx=tranche_idx))


        except Exception as e:
            logger.error(
                "Failed to report assignment",
                error=str(e),
                err_type=type(e).__name__,
                exc_info=True,
            )
            raise

    @classmethod
    async def audit_announcement(cls, assign_wrs: List[Tuple[CoreIndex, WorkReport]], tranche_idx: TrancheIndex):
        """
        This function just take a list of report which is available for auditing and assign random 10 reports to tha validator then create announcement for them.

            Arg:
                reports: List of report which just become available for auditing  [ ( Q[R?]_c )  Eq. 17.1 ]
                tranche: Current tranche index

            Return:
                set of ed21599 signature   [ Eq: 17.9, 17.10, 17.11]
        """

        from jam.audit.audit import Utils
        from jam.settings import settings
        from jam.network.node import node

        audit = Utils()

        # initial rho pending wor reports
        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()
        entropy_source = latest_block.header.entropy_source

        announcement_sign = audit.validator_announcement_statement(assign_report=assign_wrs, header=header_hash, tranche=U8(0))

        from jam.network.protocols.ce_144 import CE144Data, AuditAnnouncement, TrancheAnnouncement, FirstTrancheEvidence, Announcement, Assign, Evidence, SubsequentTrancheEvidence, NoShow

        CE144 = AuditAnnouncement()

        assignments = TypedVector[Assign]([
            Assign(core_index=core_idx, report_hash=Hash.blake2b(r.encode()))
            for core_idx, r in assign_wrs
        ])

        # -------------------- Handling Evidence based on Tranche Index --------------------------
        bandersnatch_sign  = BandersnatchVrfSignature()

        if tranche_idx == 0:
            bandersnatch_sign = audit.vrf_signature_bandersnatch(entropy_source=entropy_source, bandersnatch_key=node.b_key)
            evidence = Evidence(FirstTrancheEvidence(bandersnatch_sign))
        else:
            bandersnatch_sign = audit.vrf_signature_bandersnatch(entropy_source=entropy_source, bandersnatch_key=node.b_ke, tranche_index=tranche_idx, w_r=WorkReport())
            evidence = Evidence(
                TypedVector[SubsequentTrancheEvidence]([
                    SubsequentTrancheEvidence(
                        bandersnatch_signature=BandersnatchVrfSignature(bandersnatch_sign),
                        no_show=NoShow(
                            # TODO: FIX IT : DIKSHANT
                            validator_index=ValidatorIndex(),
                            # here will come validator index which is announcing for previous reports
                            announcement=Announcement(
                                assigned_report=assignments,
                                ed25519_signature=Ed25519Signature(ed25519)
                                # which will create using the equation 17.9 and tak validator index form mentioned in N-show
                            )
                        )
                    )
                ])
            )

        # ---------------------- Data to be transmitted ----------------------------------------
        tranche_announce = TrancheAnnouncement(
            header_hash=header_hash,
            tranches=tranche_idx,
            announcement=Announcement(
                assigned_report=assignments, ed25519_signature=announcement_sign
            )
        )

        data = CE144Data(
            len_a=U32(len(tranche_announce.encode())),
            tranche_announcement=tranche_announce,
            len_b=U32(len(evidence.encode())),
            evidence=evidence,
        )

        try:

            responses = await CE144.transmit(node=node, data=data)

            logger.debug(f"Assign Work Reports announcement transmitted successfully")

        except Exception as e:
            logger.error(
                "failed to transmitted announcement",
                error=str(e),
                error_type=type(e).__name__
        )

    @classmethod
    async def judgment_process(cls, assign_wrs: List[Tuple[CoreIndex, WorkReport]], tranche_idx:TrancheIndex):
        from jam.audit.audit import Utils
        from jam.settings import settings
        from jam.network.node import node
        from jam.operations.tranche_store import tranche_store, Tranche


        audit = Utils()

        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()


        # ------ JUDGMENT EPOCH INDEX ------
        slot = latest_block.header.slot
        logger.info(f"current judgment slot  {slot}")

        epoch_idx = int(slot // EPOCH_LENGTH)

        logger.info(f"Reports are available for judgment on this node is {len(assign_wrs)} ")

        tranche = Tranche(
            tranche_index=tranche_idx,
            header_hash=header_hash
        )

        try:
            for c, r in assign_wrs:
                wr_hash = Hash.blake2b(r.encode())

                logger.debug("Refining work report for auditing.", wr_hash=wr_hash)
                result = await audit.refine(r)

                # STORE JUDGMENT HERE ONLY FOR TRANSMITTING
                tranche_store.update_judgment(tranche=tranche, wr_hash=wr_hash, judgment=result, validator_index=node.validator_index)

                judgment_sign = audit.judgment_signature(wr=r, refine=result)

                from jam.network.protocols.ce_145 import JudgmentPublication, CE145Data, Judgment
                CE145 = JudgmentPublication()

                validity = True if result else False

                judgment = Judgment(
                    epoch_index=EpochIndex(epoch_idx),
                    validator_index=ValidatorIndex(node.validator_index),
                    validity=validity,
                    work_report_hash=WorkReportHash(wr_hash),
                    ed25519_signature=Ed25519Signature(judgment_sign),
                )

                data = CE145Data(len_a=U32(len(judgment.encode())), judgment=judgment)

                response = await CE145.transmit(node=node, data=data)

            logger.debug(f"Judgment transmitted and intercept successfully")

        except Exception as e:
            logger.error(
                f"failed to transmitted judgment",
                error=str(e),
                error_type=type(e).__name__,
            )