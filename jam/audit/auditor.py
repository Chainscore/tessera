import asyncio
import math

from tsrkit_types import U8, U32, TypedVector, Null, Bool, Uint
from jam.audit.audit import Audit
from jam.types import Ed25519Signature, HeaderHash
from jam.types.audit.audit_tranche import TrancheIndex, Tranche, OptionalReports, OptionalReport, TrancheState, CoreReport
from jam.types.protocol.core import CoreIndex, EpochIndex, ValidatorIndex
from jam.types.protocol.crypto import BandersnatchVrfSignature, Ed25519Public
from jam.types.work.report import WorkReportHash
from jam.block.block import Block
from jam.logging import get_logger
from jam.utils.constants import EPOCH_LENGTH, VALIDATORS_SUPER_MAJORITY, VALIDATORS_WONKY
from jam.network.protocols.ce_144 import NoShow, SubsequentTrancheEvidence, CoreReportHash
from jam.block.extrinsics.disputes import Verdict, Culprit, Fault, JudgementVotes, Judgement

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
        from jam.audit.utils import Utils
        from jam.audit.audit import Audit
        from jam.settings import settings
        from jam.storage.tranche_audit_store import tranche_store

        utils = Utils()
        audit = Audit()

        # --------- unwrap Tranche -------------
        curr_tranche = tranche
        tranche_index = tranche.tranche_index
        header_hash = tranche.header_hash
        validator_index = settings.validator_index

        # latest_block = Finality.load_latest(kv=settings.main_db)
        # header_hash = latest_block.header.hash()

        logger.info(f"Reports are available for judgment on this node is {len(assign_wrs)} ")

        try:
            for c_r in assign_wrs:

                wr = c_r.work_report
                wr_hash = c_r.work_report.hash()

                validity = utils.process_refine(tranche=tranche, wr_hash=wr_hash)
                ed25519_signature = audit.judgment_signature(wr=wr, validity=validity)

                validity = cls.refine2(wr=wr)
                ed25519_signature = audit.judgment_signature(wr=wr, validity=validity)


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
                # response = await CE145.transmit(data=data)
                await asyncio.create_task(CE145.transmit(data=data))

        except Exception as e:
            logger.error(
                f"Failed to build judgment inside judgment process",
                error=str(e),
                error_type=type(e).__name__,
            )

    @classmethod
    async def is_tranche(cls,
        block: Block,
        curr_tranche: Tranche,
        prev_tranche_state: TrancheState,
        ) -> TypedVector[SubsequentTrancheEvidence]:
        """
        Function to check whether the block is tranche will be continued or not.
        Builds new queue to audit and corresponding no shows and false judgments

        Args:
            block: Block to be audited
            curr_tranche: Tranche in which the block is currently in
            prev_tranche_state: last tranche state

        Returns:
            NoShows
        """
        from jam.storage.tranche_audit_store import Tranche, tranche_store
        from jam.state.state import state
        from jam.audit.audit import Audit
        from jam.settings import settings

        audit = Audit()


        header_hash = curr_tranche.header_hash
        tranche_index = curr_tranche.tranche_index
        entropy_source = BandersnatchVrfSignature(block.header.entropy_source)
        bandersnatch_private = settings.bandersnatch_private

        # ---------- Initialized NO_SHOW, UNAUDITED and NEGATIVE WR  list for this Tranche ----------
        updated_unaudited_list = OptionalReports([])
        subsequent_evidence = TypedVector[SubsequentTrancheEvidence]([])

        # ---------------------------- GET UNAUDITED LIST (q) FROM LAST TRANCHE and iterate----------
        prev_unaudited_reports = prev_tranche_state.unaudited_list

        for core_index, wr in enumerate(prev_unaudited_reports):

            rep = wr.unwrap()

            if rep == Null:
                updated_unaudited_list.append(OptionalReport(Null))

            else:
                wr_hash = rep.hash()

                if wr_hash in prev_tranche_state.records:

                    # ------------------------- WORK REPORT RECORDS FOR AUDITING  ------------------
                    audit_record = prev_tranche_state.records[wr_hash]
                    announces = audit_record.announces
                    true_votes = audit_record.true_votes
                    false_votes = audit_record.false_votes
                    no_shows = audit_record.no_shows

                    # ------------------------------ Tranche handling -----------------------------
                    # No need to update state here because there is no False judgments
                    if len(false_votes) == 0:
                        if len(no_shows) == 0:
                            if len(announces) <= len(true_votes):           #17.18.1
                                updated_unaudited_list.append(OptionalReport(Null))
                                core_report = CoreReportHash(
                                    core_index=CoreIndex(core_index),
                                    report_hash=WorkReportHash(wr_hash)
                                )
                                await tranche_store.add_to_audited_list(tranche=curr_tranche, c_w=core_report)
                            else:
                                logger.debug(f"false_votes = no_show = 0, and Error in => check true_votes >= announcement")

                        else:
                            wr_no_shows = TypedVector[NoShow]([])

                            updated_unaudited_list.append(wr)

                            bandersnatch_sign = audit.vrf_signature_bandersnatch(
                                entropy_source=entropy_source,
                                bandersnatch_key=bandersnatch_private,
                                tranche=curr_tranche,
                                w_r=rep
                            )

                            for no_show in no_shows:
                                if no_show.validator_index not in wr_no_shows:  # or need to write make it open
                                    wr_no_shows.append(no_show)

                            subsequent_evidence.append(
                                SubsequentTrancheEvidence(
                                    bandersnatch_signature=BandersnatchVrfSignature(bandersnatch_sign),
                                    no_shows=wr_no_shows
                                )
                            )

                    # -------------------------- Dispute handling ----------------------------
                    else:
                        logger.info("negative judgments trigger wala portion trigger")
                        if tranche_index == TrancheIndex(1):
                            updated_unaudited_list.append(OptionalReport(rep.unwrap()))

                        else:
                            # ---------- Handling Dispute with state -------------------------
                            before_prev = Tranche(
                                tranche_index=tranche_index- TrancheIndex(2),
                                header_hash=header_hash
                            )
                            before_prev_state = tranche_store.get_state(tranche=before_prev)
                            before_prev_records = before_prev_state.records[wr_hash]

                            #   VERY RARE CASE  =>
                            if len(before_prev_records.false_votes) == 0:
                                updated_unaudited_list.append(OptionalReport(rep.unwrap()))

                            else:
                                # ======================================================= Verdict = True =======================================================
                                if len(true_votes) >= VALIDATORS_SUPER_MAJORITY:
                                # change with len(true_votes) = VALIDATORS_SUPER_MAJORITY:

                                    # leans one valid entry in faults sequence
                                    if len(false_votes) >= 1:

                                        # epoch Index
                                        age = state.tau // EPOCH_LENGTH


                                        updated_unaudited_list.append(OptionalReport(Null))

                                        core_report = CoreReportHash(
                                            core_index=CoreIndex(core_index),
                                            report_hash=WorkReportHash(wr_hash)
                                        )

                                        await tranche_store.add_to_audited_list(tranche=curr_tranche, c_w=core_report)

                                        # E_v => verdict
                                        judgments = JudgementVotes([])
                                        for validator_index, public_key, signature in true_votes:

                                            judgment = Judgement(
                                                vote=Bool(True),
                                                index=ValidatorIndex(validator_index),
                                                signature=Ed25519Signature(signature)
                                            )

                                            judgments.append(Judgement=judgment)

                                        verdict = Verdict(
                                            target= WorkReportHash(wr_hash),
                                            age= U32(age),
                                            votes= judgments
                                        )
                                        await tranche_store.add_verdict(tranche=curr_tranche, verdict=verdict)

                                        # E_f => fault
                                        for validator_index, public_key, signature in false_votes:

                                            fault = Fault(
                                                target=WorkReportHash(wr_hash),
                                                vote=Bool(False),
                                                key=Ed25519Public(public_key),
                                                signature=Ed25519Signature(signature)
                                            )

                                            await tranche_store.add_fault(tranche=curr_tranche, fault=fault)

                                # ================================================ Verdict = False =====================================================
                                elif len(false_votes) >= VALIDATORS_SUPER_MAJORITY:
                                # change with len(true_votes) = VALIDATORS_SUPER_MAJORITY:

                                    updated_unaudited_list.append(OptionalReport(Null))

                                    core_report = CoreReportHash(
                                        core_index=CoreIndex(core_index),
                                        report_hash=WorkReportHash(wr_hash)
                                    )
                                    await tranche_store.add_to_invalid_set(tranche=curr_tranche, c_w=core_report)

                                    age = state.tau // EPOCH_LENGTH

                                    # E_v => verdict
                                    judgments = JudgementVotes([])
                                    for validator_index, public_key, signature in false_votes:
                                        judgment = Judgement(
                                            vote=Bool(False),
                                            index=ValidatorIndex(validator_index),
                                            signature=Ed25519Signature(signature)
                                        )

                                        judgments.append(Judgement=judgment)

                                    verdict = Verdict(
                                        target=WorkReportHash(wr_hash),
                                        age=U32(age),
                                        votes=judgments
                                    )

                                    await tranche_store.add_verdict(tranche=curr_tranche, verdict=verdict)

                                    # E_c ==>> culprit : True votes
                                    for validator_index, public_key, signature in true_votes:
                                        guarantee_ext = block.extrinsic.guarantees
                                        for report, slot, val_sign in guarantee_ext:
                                            if report.hash() == wr_hash:
                                                # leans two valid entry in culprits sequence
                                                if len(val_sign) >= 2:
                                                    for g_validator_index, g_signature in val_sign:
                                                        signature = g_signature
                                                        culprit = Culprit(
                                                            target=WorkReportHash(wr_hash),
                                                            key=Ed25519Public(public_key),
                                                            signature=Ed25519Signature(signature)
                                                        )
                                                        await tranche_store.add_culprit(tranche=curr_tranche, culprit=culprit)

                                # ========================= NO-VERDICT =================================================
                                elif len(true_votes) == VALIDATORS_WONKY:        # WONKY CONDITION: NONE RECEIVED VERDICT

                                    updated_unaudited_list.append(OptionalReport(Null))
                                    core_report = CoreReportHash(
                                        core_index=CoreIndex(core_index),
                                        report_hash=WorkReportHash(wr_hash)
                                    )
                                    tranche_store.add_to_wonky_set(tranche=curr_tranche, c_w=core_report)

                                    age = state.tau // EPOCH_LENGTH

                                    judgments = JudgementVotes([])
                                    for validator_index, public_key, signature in true_votes:
                                        judgment = Judgement(
                                            vote=Bool(True),
                                            index=ValidatorIndex(validator_index),
                                            signature=Ed25519Signature(signature)
                                        )
                                        judgments.append(Judgement=judgment)


                                    for validator_index, public_key, signature in false_votes:
                                        judgment = Judgement(
                                            vote=Bool(False),
                                            index=ValidatorIndex(validator_index),
                                            signature=Ed25519Signature(signature)
                                        )
                                        judgments.append(Judgement=judgment)


                                    verdict = Verdict(
                                        target=WorkReportHash(wr_hash),
                                        age=U32(age),
                                        votes=judgments
                                    )
                                    await tranche_store.add_verdict(tranche=curr_tranche, verdict=verdict)

                else:
                    updated_unaudited_list.append(OptionalReport(Null))

        # update auditable work reports in auditor state for this tranche

        await tranche_store.update_unaudited_list(
            tranche=curr_tranche,
            unaudited_reports=updated_unaudited_list
        )

        curr_state = tranche_store.get_state(tranche=curr_tranche)
        tranche_store.save_state(tranche=curr_tranche, state=curr_state)

        """
        before updating unaudited list for next tranche we check
        found_not_null = False
        for x in updated_unaudited_list:
            if x != Null:
                found_not_null = True
                logger.debug(f"Found not Null report in tranche {tranche_index}, process further for new tranche")
                break

        if not found_not_null: 
            if len(negative_wrs) == 0 and len(global_no_shows) ==0:
                logger.info(
                    f"No Work Report found for further audit in tranche {tranche_index}; proceeding to the block audited finalization process."
                )
                logger.info(
                    f"Block Audited inside in tranche 🔍",
                    # block=block,
                    header_hash=header_hash.hex(),
                    block_slot=block.header.slot,
                    curr_tranche=curr_tranche
                )
        else:
            ...
        """

        return subsequent_evidence