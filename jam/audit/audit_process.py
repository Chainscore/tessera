import asyncio
import math
from typing import List, Tuple

from sympy.logic.inference import valid
from tsrkit_types import structure, U8, Bytes, U32, TypedVector
from jam.types.protocol.core import CoreIndex

from jam.audit.audit import AuditingAndJudgement
from jam.consensus.grandpa.finality import Finality

from jam.types.work.report import WorkReport, WorkReportHash
from jam.logging import get_logger
from jam.network.node import Node
from jam.state.state import state
from jam.utils.constants import EPOCH_LENGTH
from jam.work_package.processor import Processor


# Module-specifier logger
logger = get_logger("in_core")

@structure
class AuditProcess:

    node : Node
    audit : AuditingAndJudgement

    def __init__(self, node: Node):
        from jam.settings import settings
        self.settings = settings
        self.audit = AuditingAndJudgement()
        self.node = node
        self.state = state

    async def audit_process(self):

        from jam.consensus.grandpa.finality import Finality
        settings = self.settings

        # ---------------------- Rho double dagger => Available reports ---------------------------
        rho = self.state.rho

        # ---------------------- Rho initial state ( pending wor reports)
        logger.info(f"current block header hash")
        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()

        pending_rho = self.state.load(header_hash=header_hash).rho

        # ---------------------- Block's header entropy sources -----------------------------------
        entropy = latest_block.header.entropy_source

        try:

            # pre audit reports
            logger.info(f"Get reports list which about to be audit")
            p_a_r = self.audit.report_to_be_audit(available_reports=rho, pending_report=pending_rho)

            # assignment report for auditing to validators
            logger.info(f"Work report assignment for auditing")
            reports = self.audit.verifiable_random_selection(entropy_source=entropy, bandersnatch_key=self.node.b_key, pre_audit_report=p_a_r)

            logger.debug(f"Checking assign report length {len(reports)} for eah validator")

            asyncio.create_task(self.audit_announcement(reports=reports))
            asyncio.create_task(self.judgment_process(reports=reports))


        except Exception as e:
            logger.error(f"failed to report assignment", error=e)
            raise


    async def audit_announcement(self, reports: List[Tuple[CoreIndex, WorkReport]]):
        """
            This function just take a list of report which is available for auditing and assign random 10 reports to tha validator then create announcement for them.

            Arg:
                reports: List of report which just become available for auditing  [ ( Q[R?]_c )  Eq. 17.1 ]


            Return:
                set of ed21599 signature   [ Eq: 17.9, 17.10, 17.11]

        """

        settings = self.settings

        # initial rho pending wor reports
        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()
        slot = latest_block.header.slot

        announcement = self.audit.validator_announcement_statement(assign_report=reports, header=header_hash, ed25519_public=self.node.ed_key, tranche=U8(0))

        from jam.network.protocols.ce_144 import CE144Data, AuditAnnouncement, Transmit, FirstTrancheEvidence, Announcement, Assign
        CE145 = AuditAnnouncement()

        announcement = self.audit_announcement(reports=reports)
        tranche = self.audit.tranche_index(header_slot=slot)

        announcement = Transmit(
            header_hash=header_hash,
            tranches=tranche,
            announcement=Announcement(
                assigned_report=[Assign(announcement)],
                ed25519_signature=self.node.ed_key
            )
        )

        evidence = FirstTrancheEvidence(
            bandersnatch_signature=self.node.b_key
        )

        data = CE144Data(len_a=len(U32(announcement.encode())), tranche_announcement=announcement, len_b=len(U32(evidence.encode())), evidence=evidence)

        try:
            responses = await CE145.transmit(node=self.node, data=data)


        except Exception as e:
            logger.error(
                ""
        )


    async def judgment_process(self, reports: List[Tuple[CoreIndex, WorkReport]]):
        from jam.audit.vectors.packages import hash_to_package
        settings = self.settings
        # initial rho pending wor reports
        latest_block = Finality.load_latest(kv=settings.main_db)
        slot = latest_block.header.slot


        judgment_set = set()

        get_package = None

        for c, r in reports:
            wp_hash = r.package_spec.hash
            for package in hash_to_package:
                for key, value in package.items():
                    if key == wp_hash:
                        get_package = value
                        break
                if get_package:
                    break

            result = self.audit.refine(r=r)
            signature = self.audit.judgment_signature(r=r, refine=result,ed25519_public=self.node.ed_key)
            judgment_set.add(signature)


        from jam.network.protocols.ce_145 import JudgmentPublication, CE145Data, Judgment
        CE145 = JudgmentPublication()

        epoch = math.floor(slot/EPOCH_LENGTH)

        judgment = Judgment(
            epoch_index=epoch,
            validator_index=self.node.validator_index,
            validity=U8,
            work_report_hash=WorkReportHash(),
            ed25519_signature=
        )

        data = CE145Data(len_a=U32(len(judgment.enode())), judgment=judgment)
        data = CE145.transmit(node=self.node, data=data)

        return judgment_set














