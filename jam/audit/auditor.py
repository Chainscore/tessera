import math

from jam.incore.doer import Doer
from tsrkit_types import U8, U32, TypedVector, Null, Bool, Uint
from jam.types.protocol.crypto import Ed25519Signature, HeaderHash
from jam.types.audit.audit_tranche import TrancheIndex, Tranche, CoreReport
from jam.types.protocol.core import EpochIndex
from jam.types.protocol.crypto import BandersnatchVrfSignature

from jam.types.work.report import WorkReportHash
from jam.block.block import Block
from jam.audit.audit import Audit
from jam.audit.utils import Utils

from jam.log_setup import logger
from jam.utils.constants import EPOCH_LENGTH

# Protocol Imports
from jam.network.protocols.ce_144 import (
    CE144Data,
    AuditAnnouncement,
    TrancheAnnouncement,
    FirstTrancheEvidence,
    Announcement,
    Evidence,
    SubsequentTrancheEvidence,
    CoreReportHash,
)


class Auditor(Doer):
    async def assignment_wrs(
        self,
        block: Block,
        tranche: Tranche,
        subsequent_evidence: TypedVector[SubsequentTrancheEvidence] | None = None,
    ):
        """
        The function assigns work reports for auditing to each validator
        for tranche n and triggers an announcement for the assigned reports
        """
        settings = self.settings
        from jam.storage.tranche_audit_store import tranche_store

        audit = Audit(self.jam)

        entropy = block.header.entropy_source
        curr_state = await tranche_store.get_state(tranche=tranche)

        if tranche.tranche_index == TrancheIndex(0):
            assigned_wrs = audit.verifiable_random_selection(
                entropy_source=entropy,
                bandersnatch_key=settings.bandersnatch_private,
                unaudited_report=curr_state.unaudited_list,
                tranche=tranche,
            )

        else:
            assigned_wrs = await audit.vrf_tranche(
                header_hash=tranche.header_hash,
                tranche=tranche,
                entropy=entropy,
                unaudited_wrs=curr_state.unaudited_list,
            )

        # verify this condition
        if len(assigned_wrs) == 0:
            logger.debug(
                "No Reports to audit", block=str(block), tranche=tranche, tranche_state=curr_state
            )
            return

        await self.announcement(
            block=block,
            tranche=tranche,
            assigned_wrs=assigned_wrs,
            subsequent_evidence=subsequent_evidence,
        )

    async def announcement(
        self,
        block: Block,
        tranche: Tranche,
        assigned_wrs: TypedVector[CoreReport],
        subsequent_evidence: TypedVector[SubsequentTrancheEvidence] | None = None,
    ):
        """
        This function takes a list of work reports and subsequent evidence (validators who have not given judgments),
        then creates an announcement for them using  protocol 144.

        Arg:
            block: Block on which Auditing trigger
            tranche: Current tranche index
            assigned_wrs: List of report which just become available for auditing
            subsequent_evidence:

        """

        from jam.audit.audit import Audit
        settings = self.settings
        from jam.storage.tranche_audit_store import tranche_store

        audit = Audit(self.jam)
        CE144 = AuditAnnouncement(self.jam)

        tranche_index = tranche.tranche_index
        header_hash = block.header.hash()
        entropy_source = BandersnatchVrfSignature(block.header.entropy_source)
        bandersnatch_private = settings.bandersnatch_private

        if HeaderHash(header_hash) != HeaderHash(tranche.header_hash):
            logger.error("Header hash mismatch between block and tranche")
            return

        # Prepare Announcement Data efficiently
        announcement_wrs = TypedVector[CoreReportHash](
            [
                CoreReportHash(core_index=c_r.core_index, report_hash=c_r.work_report.hash())
                for c_r in assigned_wrs
            ]
        )

        announcement_sign = audit.validator_announcement_statement(
            assign_report=assigned_wrs, header_hash=header_hash, tranche=tranche
        )

        #  Handling Evidence based on Tranche Index
        if tranche_index == TrancheIndex(0):
            bandersnatch_sign = audit.vrf_signature_bandersnatch(
                entropy_source=entropy_source,
                bandersnatch_key=bandersnatch_private,
                tranche=tranche,
            )
            evidence = Evidence(FirstTrancheEvidence(bandersnatch_sign))

        else:
            evidence = Evidence(subsequent_evidence)

        # ------------------- Save Announcement in Tranche State -----------------------------
        curr_tranche = tranche

        announce = Announcement(
            assigned_reports=announcement_wrs, ed25519_signature=announcement_sign
        )

        await tranche_store.records_announcement(
            tranche=curr_tranche, validator_index=settings.validator_index, announce=announce
        )

        # reports to be transmitted over the network
        tranche_announce = TrancheAnnouncement(
            header_hash=header_hash,
            tranche=tranche_index,
            announcement=Announcement(
                assigned_reports=announcement_wrs, ed25519_signature=announcement_sign
            ),
        )

        data = CE144Data(
            len_a=Uint[32](len(tranche_announce.encode())),
            tranche_announcement=tranche_announce,
            len_b=Uint[32](len(evidence.encode())),
            evidence=evidence,
        )

        try:
            await CE144.transmit(data=data)
            await self.judgment_process(block=block, tranche=tranche, assign_wrs=assigned_wrs)

        except Exception as e:
            logger.error(
                "Unexpected error while transmitting CE144 announcement",
                error=str(e),
                error_type=type(e).__name__,
            )

    async def judgment_process(
        self,
        block: Block,
        tranche: Tranche,
        assign_wrs: TypedVector[CoreReport] | None = None,
    ):
        """
        This function takes a list of work reports, creates a judgment (Valid or Invalid) for each,
        and transmits the individual judgments to other validators using protocol 145.

        Arg:
            block: Block on which Auditing trigger
            tranche: Current tranche index
            assigned_wrs: List of report which just become available for judgments
        """
        settings = self.settings
        from jam.storage.tranche_audit_store import tranche_store
        from jam.audit.audit import Audit
        from jam.network.protocols.ce_145 import JudgmentPublication, CE145Data, Judgment

        audit = Audit(self.jam)
        CE145 = JudgmentPublication(self.jam)

        curr_tranche = tranche
        validator_index = settings.validator_index

        if not assign_wrs:
            logger.info("No assigned work reports for judgment", tranche=tranche)
            return

        logger.debug(f"Reports are available for judgment on this node is {len(assign_wrs)}")

        try:
            for c_r in assign_wrs:
                wr = c_r.work_report
                wr_hash = c_r.work_report.hash()

                validity = await audit.refine(wr=wr)
                ed25519_signature = audit.judgment_signature(wr_hash=wr_hash, validity=validity)

                state = self.state

                epoch_index = EpochIndex(math.floor(state.tau / EPOCH_LENGTH))

                judgment = Judgment(
                    epoch_index=epoch_index,
                    validator_index=validator_index,
                    validity=validity,
                    work_report_hash=WorkReportHash(wr_hash),
                    ed25519_signature=Ed25519Signature(ed25519_signature),
                )

                #  Save judgment in Tranche State
                await tranche_store.update_judgment(
                    tranche=curr_tranche, judgment=judgment, ed25519_public=settings.ed25519_public
                )

                data = CE145Data(len_a=U32(len(judgment.encode())), judgment=judgment)
                response = await CE145.transmit(data=data)

        except Exception as e:
            logger.error(
                "Unexpected error while building or transmitting judgments",
                error=str(e),
                error_type=type(e).__name__,
            )
