import math
from typing import List, Tuple

from tsrkit_types import U8, U32, TypedVector, Null, Bool

from jam.audit.utils import Utils
from jam.types import Ed25519Signature, HeaderHash
from jam.finality.finality import Finality
from jam.types.audit.tranche import TrancheIndex, Tranche, OptionalReports, OptionalReport
from jam.types.protocol.core import CoreIndex, EpochIndex
from jam.types.protocol.crypto import BandersnatchVrfSignature
from jam.types.work.report import WorkReport, WorkReportHash
from jam.block.block import Block

from jam.logging import get_logger
from jam.utils.constants import EPOCH_LENGTH
from jam.network.protocols.ce_144 import NoShow, NoShows

# Module-specifier logger
logger = get_logger("auditor")


class Auditor:
    async def audit(self, block: Block, tranche: Tranche, no_shows: NoShows = None):
        """
        Main Function to trigger auditing for nth tranche (n >= 0)
        """
        from jam.settings import settings
        from jam.storage.tranche_store import tranche_store

        utils = Utils()

        entropy = block.header.entropy_source

        curr_state = tranche_store.get_state(tranche)

        if tranche.tranche_index == TrancheIndex(0):
            assigned_wrs = utils.verifiable_random_selection(
                entropy_source=entropy,
                bandersnatch_key=settings.bandersnatch_private,
                unaudited_report=curr_state.unaudited_list,
                tranche=tranche,
            )
        else:
            assigned_wrs = utils.vrf_tranche(
                header_hash=tranche.header_hash,
                tranche=tranche,
                entropy=entropy,
                unaudited_wrs=curr_state.unaudited_list,
            )

        if len(assigned_wrs) == 0:
            logger.debug("No Reports to audit", block=str(block), tranche=tranche, tranche_state=curr_state.to_json())
            return

        logger.debug("ASSIGNED REPORTS", block=str(block), tranche=tranche, tranche_state=curr_state.to_json(), assigned_reps=assigned_wrs)
        await self.announce(block, tranche, assigned_wrs, no_shows)
        ...

    @classmethod
    async def announce(
        cls,
        block: Block,
        tranche: Tranche,
        assigned_wrs: List[Tuple[CoreIndex, WorkReport]],
        no_shows: TypedVector[NoShow] = None,
    ):
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

        audit = Utils()

        # --------------------------------------------- CONDITION CHECK ------------------------------------------------
        if HeaderHash(block.header.hash()) != HeaderHash(tranche.header_hash):
            logger.info("Block's header_has and tranche header_hash are different")
            return

        # ---------------------------------------------- DEFINES VALUE --------------------------------------------------
        tranche_index = tranche.tranche_index
        header_hash = HeaderHash(block.header.hash())
        entropy_source = BandersnatchVrfSignature(block.header.entropy_source)

        # ------------------------------------------ BUILDING PROTOCOL DATA --------------------------------------------
        from jam.network.protocols.ce_144 import (
            CE144Data,
            AuditAnnouncement,
            TrancheAnnouncement,
            FirstTrancheEvidence,
            Announcement,
            AssignedReport,
            Evidence,
            SubsequentTrancheEvidence,
            NoShow,
        )

        CE144 = AuditAnnouncement()

        # ------------------------------------- VALIDATOR ANNOUNCEMENT AND STATEMENT -----------------------------------
        assignments = TypedVector[AssignedReport](
            [
                AssignedReport(core_index=core_idx, report_hash=r.hash())
                for core_idx, r in assigned_wrs
            ]
        )

        announcement_sign = audit.validator_announcement_statement(
            assign_report=assigned_wrs, header_hash=header_hash, tranche=tranche
        )

        # -------------------- Handling Evidence based on Tranche Index --------------------------
        bandersnatch_sign = BandersnatchVrfSignature(b"")

        if tranche_index == TrancheIndex(0):
            bandersnatch_sign = audit.vrf_signature_bandersnatch(
                entropy_source=entropy_source,
                bandersnatch_key=settings.bandersnatch_private,
                tranche=tranche,
            )
            evidence = Evidence(FirstTrancheEvidence(bandersnatch_sign))
        else:
            bandersnatch_sign = audit.vrf_signature_bandersnatch(
                entropy_source=entropy_source,
                bandersnatch_key=settings.bandersnatch_private,
                tranche=tranche,
            )
            evidence = Evidence(
                TypedVector[SubsequentTrancheEvidence](
                    [
                        SubsequentTrancheEvidence(
                            bandersnatch_signature=BandersnatchVrfSignature(bandersnatch_sign),
                            no_show=no_shows,
                        )
                    ]
                )
            )

        # ---------------------- Data to be transmitted ----------------------------------------
        tranche_announce = TrancheAnnouncement(
            header_hash=header_hash,
            tranche=tranche_index,
            announcement=Announcement(
                assigned_reports=assignments,
                ed25519_signature=announcement_sign
            ),
        )

        data = CE144Data(
            len_a=U32(len(tranche_announce.encode())),
            tranche_announcement=tranche_announce,
            len_b=U32(len(evidence.encode())),
            evidence=evidence,
        )

        try:
            responses = await CE144.transmit(data=data)

            if responses:
                await cls.judgment_process(assign_wrs=assigned_wrs, tranche=tranche)

            logger.debug(f"Assign Work Reports announcement transmitted successfully")

        except Exception as e:
            logger.error(
                "failed to transmitted announcement", error=str(e), error_type=type(e).__name__
            )

    @classmethod
    async def judgment_process(
        cls, assign_wrs: List[Tuple[CoreIndex, WorkReport]], tranche: Tranche
    ):
        from jam.audit.utils import Utils
        from jam.settings import settings
        from jam.storage.tranche_store import tranche_store

        audit = Utils()

        latest_block = Finality.load_latest(kv=settings.main_db)
        header_hash = latest_block.header.hash()

        # ------ JUDGMENT EPOCH INDEX ------
        slot = latest_block.header.slot
        epoch_idx = EpochIndex(math.floor(slot / EPOCH_LENGTH))

        logger.info(f"Reports are available for judgment on this node is {len(assign_wrs)} ")

        try:
            for c, r in assign_wrs:
                wr_hash = r.hash()

                is_valid = await audit.refine(r)

                # STORE JUDGMENT HERE ONLY FOR TRANSMITTING
                tranche_store.update_judgment(
                    tranche=tranche,
                    wr_hash=wr_hash,
                    judgment=is_valid,
                    validator_index=settings.validator_index,
                )

                judgment_sign = audit.judgment_signature(wr=r, refine=is_valid)

                from jam.network.protocols.ce_145 import JudgmentPublication, CE145Data, Judgment

                CE145 = JudgmentPublication()

                judgment = Judgment(
                    epoch_index=epoch_idx,
                    validator_index=settings.validator_index,
                    validity=Bool(True),
                    work_report_hash=WorkReportHash(wr_hash),
                    ed25519_signature=Ed25519Signature(judgment_sign),
                )

                data = CE145Data(len_a=U32(len(judgment.encode())), judgment=judgment)

                response = await CE145.transmit(data=data)

            logger.debug(f"Judgment transmitted successfully")

        except Exception as e:
            logger.error(
                f"failed to transmitted judgment",
                error=str(e),
                error_type=type(e).__name__,
            )

    @classmethod
    def is_audited(cls, block: Block, tranche: Tranche) -> NoShows:
        """
        Function to check whether the block is audited or not.
        Builds new queue to audit and corresponding no shows

        Args:
            block: Block to be audited
            tranche: Tranche in which the block is currently in

        Returns:
            NoShows
        """
        from jam.storage.tranche_store import Tranche, tranche_store

        logger.debug("Checking whether the block is audited or not.")
        header_hash = tranche.header_hash
        tranche_index = tranche.tranche_index

        no_shows = NoShows([])

        prev_tranche = Tranche(
            header_hash=header_hash, tranche_index=tranche_index - TrancheIndex(1)
        )

        prev_state = tranche_store.get_state(tranche=prev_tranche)

        # GET Q FROM PREVIOUS TRANCHE
        unaudited_reports = prev_state.unaudited_list

        updated_unaudited_list = OptionalReports([])

        for wr in unaudited_reports:
            rep = wr.unwrap()

            if rep == Null:
                updated_unaudited_list.append(OptionalReport(Null))

            else:
                wr_hash = rep.hash()

                if wr_hash in prev_state.records:
                    audit_record = prev_state.records[wr_hash]

                    true_votes = audit_record.true_votes
                    false_votes = audit_record.false_votes
                    announces = audit_record.announces
                    no_votes = audit_record.no_votes

                    # GENERATE Q (UN_AUDITED_LIST FOR NEXT TRANCHES)
                    # HERE WE WRITE LOGIC FOR NO_SHOW and IT'S CONDITION
                    # 1. validator index exist in no_votes
                    # 2. validator index exist in false votes (just by limited validators)
                    # 3. false_votes audit by all the validators

                    # TODO: Possible issues: instead of length, properly check subsets
                    if (
                        len(true_votes) == len(announces)
                        and len(false_votes) == 0
                        and len(no_votes) == 0
                    ):
                        updated_unaudited_list.append(OptionalReport(Null))

                    elif (
                        len(true_votes) != len(announces)
                        and len(no_votes) != 0
                        or len(false_votes) != 0
                    ):
                        updated_unaudited_list.append(OptionalReport(rep))

                        # BUILD NO_SHOW HERE
                        if (
                            len(announces) > len(true_votes) + len(false_votes)
                            and len(no_votes) != 0
                        ):
                            for v in no_votes:
                                ann_list = tranche_store.get_set_announcement(
                                    tranche=prev_tranche, validator_index=v
                                )
                                if v not in [no_show.validator_index for no_show in no_shows]:
                                    no_shows.append(
                                        NoShow(validator_index=v, announcement=ann_list)
                                    )
                else:
                    logger.warning(" Report not exist in audit records of Tranche state !!")

        # UPDATE WORK REPORTS IN Q ANDB
        current_tranche = Tranche(header_hash=header_hash, tranche_index=tranche_index)

        tranche_store.add_to_unaudited(
            tranche=current_tranche, unaudited_reports=updated_unaudited_list
        )

        return no_shows
