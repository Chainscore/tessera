import asyncio
import math
from typing import List, Tuple

from tsrkit_types import structure, U8, U32, TypedVector, Option, Null, Bool

from jam.block import Block
from jam.types import ValidatorIndex, Ed25519Signature, WorkReports

from jam.finality.finality import Finality
from jam.state.state import State

from jam.types.audit.tranche import TrancheIndex, Tranche
from jam.types.protocol.core import CoreIndex, EpochIndex
from jam.types.protocol.crypto import Hash, BandersnatchVrfSignature
from jam.types.state.rho import WorkReportState
from jam.types.work.report import WorkReport, WorkReportHash

from jam.logging import get_logger
from jam.utils.constants import EPOCH_LENGTH
from jam.network.protocols.ce_144 import NoShow, AssignedReport
from jam.storage.tranche_store import TrancheStore, Tranche


# Module-specifier logger
logger = get_logger("auditor")

@structure
class Auditor:

    @classmethod
    async def audit(cls, block: Block, tranche: Tranche):
        from jam.audit.utils import Utils

        # from jam.state.state import state
        from jam.settings import settings
        from jam.network.node import node
        from jam.storage.tranche_store import tranche_store, Tranche

        audit = Utils()

        tranche_idx = int(tranche.tranche_index)
        header_hash = tranche.header_hash

        tranche_state = tranche_store._get_state(tranche)
        reports_queue = tranche_state.unaudited_list

        # TODO: Calculate only if tranche > 0
        prev_tranche = tranche
        prev_tranche.tranche_index = TrancheIndex(tranche_idx - 1)
        prev_tranche_state = tranche_store._get_state(prev_tranche)

        entropy = block.header.entropy_source

        try:
            # Pre Audit Reports
            logger.info(f"Fetching auditable reports per core")
            if tranche_idx == 0:

                assigned_reports = audit.verifiable_random_selection(entropy_source=entropy,
                                                                     bandersnatch_key=node.b_key,
                                                                     pre_audit_report=reports_queue)

                logger.info(
                    f"Checking assign report length {len(assigned_reports)} for each validator"
                )

            else:
                assigned_reports = WorkReports([])

            tranche_state.assigned_wrs = assigned_reports
            asyncio.create_task(cls.audit_announcement(assign_wrs=assigned_reports, tranche_idx=tranche_idx))
            asyncio.create_task(cls.judgment_process(assign_wrs=assigned_reports, tranche_idx=tranche_idx))


        except Exception as e:
            logger.error(
                "Failed to report assignment",
                error=str(e),
                err_type=type(e).__name__,
                exc_info=True,
            )
            raise

    @classmethod
    async def announce_judgment(cls, assign_wrs: List[Tuple[CoreIndex, WorkReport]], tranche: Tranche, no_shows: TypedVector[NoShow] = None):
        """
        This function just take a list of report which is available for auditing and assign random 10 reports to tha validator then create announcement for them.

            Arg:
                reports: List of report which just become available for auditing  [ ( Q[R?]_c )  Eq. 17.1 ]
                tranche: Current tranche index

            Return:
                set of ed21599 signature   [ Eq: 17.9, 17.10, 17.11]
        """

        from jam.audit.utils import Utils
        from jam.settings import settings
        from jam.network.node import node

        audit = Utils()

        tranche_index = tranche.tranche_index

        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()
        entropy_source = latest_block.header.entropy_source

        from jam.network.protocols.ce_144 import CE144Data, AuditAnnouncement, TrancheAnnouncement, FirstTrancheEvidence, Announcement, Assign, Evidence, SubsequentTrancheEvidence, NoShow
        CE144 = AuditAnnouncement()

        # ------------------------------------- Validator Announcement and Statement ---------------------------------------
        assignments = TypedVector[AssignedReport]([
            AssignedReport(core_index=core_idx, report_hash=Hash.blake2b(r.encode()))
            for core_idx, r in assign_wrs
        ])

        announcement_sign = audit.validator_announcement_statement(assign_report=assign_wrs, header=header_hash, tranche=U8(0))

        # -------------------- Handling Evidence based on Tranche Index --------------------------
        bandersnatch_sign  = BandersnatchVrfSignature(b"")

        if tranche_index == TrancheIndex(0):
            bandersnatch_sign = audit.vrf_signature_bandersnatch(entropy_source=entropy_source, bandersnatch_key=node.b_key)
            evidence = Evidence(FirstTrancheEvidence(bandersnatch_sign))
        else:
            bandersnatch_sign = audit.vrf_signature_bandersnatch(entropy_source=entropy_source, bandersnatch_key=node.b_ke, tranche_index=tranche_idx, w_r=WorkReport())
            evidence = Evidence(
                TypedVector[SubsequentTrancheEvidence]([
                    SubsequentTrancheEvidence(
                        bandersnatch_signature=BandersnatchVrfSignature(bandersnatch_sign),
                        no_show=no_shows
                    )
                ])
            )

        # ---------------------- Data to be transmitted ----------------------------------------
        tranche_announce = TrancheAnnouncement(
            header_hash=header_hash,
            tranche=tranche_index,
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

            if responses:

                no_show_report = await cls.judgment_process(assign_wrs=assign_wrs, tranche=tranche)


            logger.debug(f"Assign Work Reports announcement transmitted successfully")

        except Exception as e:
            logger.error(
                "failed to transmitted announcement",
                error=str(e),
                error_type=type(e).__name__
        )

    @classmethod
    async def judgment_process(cls, assign_wrs: List[Tuple[CoreIndex, WorkReport]], tranche:Tranche):
        from jam.audit.utils import Utils
        from jam.settings import settings
        from jam.network.node import node
        from jam.storage.tranche_store import tranche_store, Tranche


        audit = Utils()

        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()

        # ------ JUDGMENT EPOCH INDEX ------
        slot = latest_block.header.slot
        epoch_idx = EpochIndex(math.floor(slot / EPOCH_LENGTH))

        logger.info(f"Reports are available for judgment on this node is {len(assign_wrs)} ")


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

                judgment = Judgment(
                    epoch_index=epoch_idx,
                    validator_index=ValidatorIndex(node.validator_index),
                    validity=Bool(True),
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