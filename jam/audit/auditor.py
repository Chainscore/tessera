import math
from tsrkit_types import U8, U32, TypedVector, Null, Bool, Uint
from jam.audit.audit import Audit
from jam.types.protocol.crypto import Ed25519Signature, HeaderHash
from jam.types.audit.audit_tranche import TrancheIndex, Tranche, CoreReport
from jam.types.protocol.core import EpochIndex
from jam.types.protocol.crypto import BandersnatchVrfSignature
from jam.types.work.report import WorkReportHash, WorkReport
from jam.block.block import Block
from jam.logging import get_logger
from jam.utils.constants import EPOCH_LENGTH
from jam.network.protocols.ce_144 import SubsequentTrancheEvidence, CoreReportHash

# Module-specifier logger
logger = get_logger("auditor")


class Auditor:
    async def assignment_wrs(
        self,
        block: Block,
        tranche: Tranche,
        subsequent_evidence: TypedVector[SubsequentTrancheEvidence] = None,
    ):
        """
        Main Function to trigger auditing for nth tranche (n >= 0)
        """
        from jam.settings import settings
        from jam.storage.tranche_audit_store import tranche_store

        audit = Audit()

        entropy = block.header.entropy_source

        tranche_index = tranche.tranche_index
        header_hash = tranche.header_hash

        # fetch current state
        curr_state = tranche_store.get_state(tranche=tranche)

        if tranche_index == TrancheIndex(0):
            assigned_wrs = audit.verifiable_random_selection(
                entropy_source=entropy,
                bandersnatch_key=settings.bandersnatch_private,
                unaudited_report=curr_state.unaudited_list,
                tranche=tranche,
            )

        else:
            assigned_wrs = audit.vrf_tranche(
                header_hash=tranche.header_hash,
                tranche=tranche,
                entropy=entropy,
                unaudited_wrs=curr_state.unaudited_list,
            )

        # verify this condition
        if len(assigned_wrs) == 0:
            logger.debug("No Reports to audit", block=str(block), tranche=tranche, tranche_state=curr_state)

            return

        # logger.debug("ASSIGNED REPORTS", block=str(block), tranche=tranche, tranche_state=curr_state.to_json(), assigned_reps=assigned_wrs)
        await self.announcement(block=block, tranche=tranche, assigned_wrs=assigned_wrs, subsequent_evidence=subsequent_evidence)
        ...

    @classmethod
    async def announcement(
        cls,
        block: Block,
        tranche: Tranche,
        assigned_wrs: TypedVector[CoreReport],
        subsequent_evidence: TypedVector[SubsequentTrancheEvidence] = None,
    ):
        """
        This function just take a list of report which is available for auditing and assign random 10 reports to tha validator then create announcement for them.

            Arg:
                reports: List of report which just become available for auditing  [ ( Q[R?]_c )  Eq. 17.1 ]
                tranche: Current tranche index

            Return:
                set of ed21599 signature   [ Eq: 17.9, 17.10, 17.11]
        """

        from jam.audit.audit import Audit
        from jam.settings import settings
        from jam.storage.tranche_audit_store import tranche_store

        audit = Audit()

        # --------------------------------------------- CONDITION CHECK ---------------------
        if HeaderHash(block.header.hash()) != HeaderHash(tranche.header_hash):
            logger.info("Block's header_has and tranche header_hash are different")
            return

        # ---------------------------------------------- DEFINES VALUE -----------------------
        tranche_index = tranche.tranche_index
        header_hash = block.header.hash()
        entropy_source = BandersnatchVrfSignature(block.header.entropy_source)
        bandersnatch_private = settings.bandersnatch_private

        # ------------------------------------------ BUILDING PROTOCOL DATA ------------------
        from jam.network.protocols.ce_144 import (
            CE144Data,
            AuditAnnouncement,
            TrancheAnnouncement,
            FirstTrancheEvidence,
            Announcement,
            Evidence,
        )

        CE144 = AuditAnnouncement()

        # ------------------------------------- VALIDATOR ANNOUNCEMENT AND STATEMENT ---------
        announcement_wrs = TypedVector[CoreReportHash]([
            CoreReportHash(
                core_index=c_r.core_index,
                report_hash=c_r.work_report.hash()
            )
            for c_r in assigned_wrs
        ])

        announcement_sign = audit.validator_announcement_statement(
            assign_report=assigned_wrs,
            header_hash=header_hash,
            tranche=tranche
        )

        # -------------------- Handling Evidence based on Tranche Index ----------------------

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
                assigned_reports=announcement_wrs,
                ed25519_signature=announcement_sign
        )

        tranche_store.records_announcement(
            tranche=curr_tranche,
            validator_index=settings.validator_index,
            announce=announce
        )

        # ---------------------- Data to be transmitted --------------------------------------
        tranche_announce = TrancheAnnouncement(
            header_hash=header_hash,
            tranche=tranche_index,
            announcement=Announcement(
                assigned_reports=announcement_wrs,
                ed25519_signature=announcement_sign
            )
        )

        data = CE144Data(
            len_a=Uint[32](len(tranche_announce.encode())),
            tranche_announcement=tranche_announce,
            len_b=Uint[32](len(evidence.encode())),
            evidence=evidence,
        )

        try:
            responses = await CE144.transmit(data=data)

            await cls.judgment_process(block=block, tranche=tranche,assign_wrs=assigned_wrs)

        except Exception as e:
            logger.error(
                "Failed to build announcement inside announcement function ", error=str(e), error_type=type(e).__name__
            )

    @classmethod
    async def judgment_process(
        cls,
        block: Block,
        tranche: Tranche,
        assign_wrs: TypedVector[CoreReport] = None,
    ):
        """
        description come
        """
        from jam.settings import settings
        from jam.storage.tranche_audit_store import tranche_store
        from jam.audit.utils import Utils
        from jam.audit.audit import Audit


        # --------- unwrap Tranche -------------
        curr_tranche = tranche
        tranche_index = tranche.tranche_index
        header_hash = tranche.header_hash
        validator_index = settings.validator_index


        logger.info(f"Reports are available for judgment on this node is {len(assign_wrs)}")

        cnt = 0

        try:
            for c_r in assign_wrs:

                wr = c_r.work_report
                wr_hash = c_r.work_report.hash()

                validity = Utils.process_refine(tranche=tranche, wr_hash=wr_hash)
                ed25519_signature = Audit.judgment_signature(wr=wr, validity=validity)

                # ---------------------------------- BUILDING PROTOCOL DATA ----------------------
                from jam.network.protocols.ce_145 import JudgmentPublication, CE145Data, Judgment

                CE145 = JudgmentPublication()

                # --------------------------- JUDGMENT EPOCH INDEX ------------------------------
                from jam.state.state import state
                epoch_index = EpochIndex(math.floor(state.tau / EPOCH_LENGTH))

                judgment = Judgment(
                    epoch_index=epoch_index,
                    validator_index=validator_index,
                    validity=validity,
                    work_report_hash=WorkReportHash(wr_hash),
                    ed25519_signature=Ed25519Signature(ed25519_signature),
                )

                # ------------------- Save judgment in Tranche State ----------------------------

                await tranche_store.update_judgment(
                    tranche=curr_tranche,
                    judgment=judgment,
                    ed25519_public=settings.ed25519_public
                )

                data = CE145Data(len_a=U32(len(judgment.encode())), judgment=judgment)
                response = await CE145.transmit(data=data)

        except Exception as e:
            logger.error(
                f"Failed to build judgment inside judgment process",
                error=str(e),
                error_type=type(e).__name__,
            )

    @classmethod
    def refine2(cls,  wr: WorkReport) -> U8:
        wr_hash = wr.hash()
        from jam.audit.dummy import get_work_package_by_rep_hash
        validity = get_work_package_by_rep_hash(filepath="/home/dikshant441/Desktop/jam/tessera/jam/combined.json", rep_hash=wr_hash)

        return U8(validity)