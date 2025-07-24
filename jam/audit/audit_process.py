import asyncio
import math
from typing import List, Tuple

from tsrkit_types import structure, U8, U32, TypedVector, Option, Null

from jam.types import Hash, BandersnatchVrfSignature, ValidatorIndex
from jam.types.protocol.core import CoreIndex, EpochIndex,TrancheIndex

from jam.finality.finality import Finality

from jam.types.work.report import WorkReportHash
from jam.logging import get_logger
from jam.utils.constants import EPOCH_LENGTH
from jam.audit.q import sample_work_reports_with_nulls, get_work_package_by_rep_hash
from tests.unit.wp.types import WorkReport


# Module-specifier logger
logger = get_logger("in_core")


@structure
class AuditProcess:
    @classmethod
    async def audit_process(cls, newly_avail_wrs: List[Option[WorkReport]], tranche_idx:TrancheIndex):
        from jam.audit.audit import AuditingAndJudgement

        # from jam.state.state import state
        from jam.settings import settings
        from jam.network.node import node
        from jam.operations.tranche_store import tranche_store, Tranche


        audit = AuditingAndJudgement()

        # ---------------------- Rho initial state ( pending wor reports) -------------------------
        logger.info(f"Current Block header hash")
        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()

        logger.info(f"Get rho pending state (Initial state)")
        # pending_rho_ = state.load(header_hash=header_hash).rho

        # ---------------------- Block's header entropy sources -----------------------------------
        entropy = latest_block.header.entropy_source

        final_list = sample_work_reports_with_nulls("jam/combine.json",total_items=12, null_count=4)

        try:
            # pre audit reports
            logger.info(f"Get reports list which about to be audit")

            p_a_r = audit.report_to_be_audit(
                pending_wrs=final_list, newly_avail_wrs=newly_avail_wrs
            )

            # ---------------------- Update the q in tranche store ------------------------------------
            tranche = Tranche(
                tranche_index=tranche_idx,
                header_hash=header_hash
            )

            tranche_store.add_to_unaudited(tranche=tranche, p_a_r=p_a_r)

            # assignment report for auditing to validators
            logger.info(f"Work report assignment for auditing")

            reports = audit.verifiable_random_selection(entropy_source=entropy, bandersnatch_key=node.b_key, pre_audit_report=p_a_r)

            logger.info(
                f"Checking assign report length {len(reports)} for each validator"
            )

            asyncio.create_task(AuditProcess.audit_announcement(assign_wrs=reports, tranche_idx=tranche_idx))
            asyncio.create_task(AuditProcess.judgment_process(assign_wrs=reports, tranche_idx=tranche_idx))


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

        from jam.audit.audit import AuditingAndJudgement
        from jam.settings import settings
        from jam.network.node import node

        audit = AuditingAndJudgement()

        # initial rho pending wor reports
        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()

        announcement_sign = audit.validator_announcement_statement(assign_report=assign_wrs, header=header_hash, tranche=U8(0))

        from jam.network.protocols.ce_144 import CE144Data, AuditAnnouncement, Transmit, FirstTrancheEvidence, Announcement, Assign, Evidence
        from jam.operations.tranche_store import tranche_store, Tranche


        CE144 = AuditAnnouncement()


        assignments = TypedVector[Assign]([
            Assign(core_index=core_idx, report_hash=Hash.blake2b(r.encode()))
            for core_idx, r in assign_wrs
        ])

        announcement = Transmit(
            header_hash=header_hash,
            tranches=tranche_idx,
            announcement=Announcement(
                assigned_report=assignments, ed25519_signature=announcement_sign
            ),
        )

        # siggnature = audit.vrf_signature_bandersnatch(entropy_source=, bandersnatch_key=, tranche_index=, )

        # Handling Evidence based on current tranches
        # if tranche_idx == 0:
        #     evidence = Evidence(FirstTrancheEvidence(sign))
        # else:
        #     evidence = Evidence(SubsequentTrancheEvidence())

        sign = BandersnatchVrfSignature(
            b'\x97\xf1\xd3\xa71\x97\xd7\x94&\x95c\x8cO\xa9\xac\x0f\xc3h\x8cO\x97t\xb9\x05\xa1N:?\x17\x1b\xacXlU\xe8?\xf9z\x1a\xef\xfb:\xf0\n\xdb"\xc6\xbb\x97\xf1\xd3\xa71\x97\xd7\x94&\x95c\x8cO\xa9\xac\x0f\xc3h\x8cO\x97t\xb9\x05\xa1N:?\x17\x1b\xacXlU\xe8?\xf9z\x1a\xef\xfb:\xf0\n\xdb"\xc6\xbb')

        evidence = Evidence(FirstTrancheEvidence(sign))


        data = CE144Data(
            len_a=U32(len(announcement.encode())),
            tranche_announcement=announcement,
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
        from jam.audit.audit import AuditingAndJudgement
        from jam.settings import settings
        from jam.network.node import node
        from jam.operations.tranche_store import tranche_store, Tranche


        audit = AuditingAndJudgement()

        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()
        slot = latest_block.header.slot
        logger.info(f"current judgment slot  {slot}")

        epoch = math.floor(slot / EPOCH_LENGTH)

        logger.info(f"Reports are available for judgment on this node is {len(assign_wrs)} ")

        tranche = Tranche(
            tranche_index=tranche_idx,
            header_hash=header_hash
        )

        try:
            for c, r in assign_wrs:
                wr_hash = Hash.blake2b(r.encode())

                package, core, extrinsic  = get_work_package_by_rep_hash(filepath="jam/combine.json", rep_hash=wr_hash)

                result = await audit.audit_refine(p=package, c=core, e=extrinsic, wr=r, node_index=node.validator_index)

                # STORE JUDGMENT HERE ONLY FOR TRANSMITTING
                tranche_store.update_judgment(tranche=tranche, wr_hash=wr_hash, judgment=result, validator_index=node.validator_index)

                judgment_sign = audit.judgment_signature(wr=r, refine=result)

                from jam.network.protocols.ce_145 import JudgmentPublication, CE145Data, Judgment
                CE145 = JudgmentPublication()

                validity = U8(1) if result else U8(0)

                judgment = Judgment(
                    epoch_index=EpochIndex(0),
                    validator_index=node.validator_index,
                    validity=validity,
                    work_report_hash=WorkReportHash(wr_hash),
                    ed25519_signature=judgment_sign,
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
