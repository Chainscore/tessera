import asyncio
import math
from tsrkit_types import U32, Uint, U8, Null, TypedVector, Bool
from jam.block.extrinsics.disputes import DisputesExtrinsic, Verdicts, Culprits, Faults
from jam.block.block import Block
from jam.types.work.report import WorkReportHash, WorkReport, WorkReports
from jam.types.audit.audit_tranche import TrancheIndex, Tranche, OptionalReports, OptionalReport, TrancheState, CoreReport, Records, AuditRecord
from jam.types.protocol.crypto import BandersnatchVrfSignature, Ed25519Public, Ed25519Signature, HeaderHash
from jam.types.protocol.core import CoreIndex, EpochIndex, ValidatorIndex
from jam.audit.audit import Audit
from jam.network.protocols.ce_144 import NoShow, SubsequentTrancheEvidence, CoreReportHash
from jam.utils.constants import EPOCH_LENGTH, VALIDATORS_SUPER_MAJORITY, VALIDATORS_WONKY
from jam.block.extrinsics.disputes import Verdict, Culprit, Fault, JudgementVotes, Judgement
from jam.log_setup import logger


class Utils:

    @classmethod
    async def fetch_report(cls, wr_hash: WorkReportHash) -> WorkReport | None:
        """
        Fetch Work Report.
        1. Check in ReportDA
        2. Request from other Auditor via protocol 136 if not found.

        Args:
            wr_hash: Work Report Hash

        Returns:
            WorkReport if found
        Raises:
            KeyError if not found anywhere
            NetworkingError if protocol 136 failed
        """

        from jam.settings import settings
        from jam.storage.da.reports import ReportsDA
        from jam.network.protocols.ce_136 import WorkReportRequest, CE136Data

        CE136 = WorkReportRequest()

        try:
            reports_da = ReportsDA(settings.d3l)
            wr = reports_da.get(wr_hash=wr_hash)
            print("wr inside fetch_report via reportsDA", settings.NODE_NAME, wr)

            if wr is not None:
                return wr

        except KeyError:
            logger.info(
                "WorkReport not in ReportsDA, falling back to protocol 136", wr_hash=wr_hash
            )

        # Request via protocol 136
        try:
            data = CE136Data(len=U32(len(wr_hash.encode())), work_report_hash=wr_hash)

            wr = await CE136.transmit(data=data, assurers=None)
            print("wr inside fetch_report via protocol 136", wr)

            if wr.hash() != wr_hash:
                logger.error(
                    "Received mismatched WorkReport from protocol 136",
                    expected=wr_hash,
                    got=wr.hash(),
                )
                return None

            return wr

        except Exception as e:
            logger.debug("Failed to fetch Work Report via protocol 136", wr_hash=wr_hash, exc=e)

    @classmethod
    async def process_refine(cls, wr_hash: WorkReportHash, tranche: Tranche) -> U8 | None:
        """
        Check whether the given Work Report has already been refined.

        Refinement can be skipped if either:
          1. The report was refined in any previous tranche.
          2. The report was already refined during the guarantee process.
          3. If neither condition (1) nor (2) is true, then perform refinement now.

        Args:
            wr_hash: Work Report Hash
            tranche: Current Process Tranche_Index

        Return:
            Validity (Single byte => U8(1) OR U8(0) )
        """

        from jam.settings import settings
        from jam.storage.tranche_audit_store import tranche_store

        tranche_index = tranche.tranche_index
        header_hash = tranche.header_hash
        validator_index = settings.validator_index

        state = tranche_store.get_state(tranche=tranche)

        # Get state records
        audit_record = state.records[wr_hash]
        announces = audit_record.announces
        true_votes = audit_record.true_votes
        false_votes = audit_record.false_votes

        if validator_index in true_votes:
            logger.info(f"already true judgment given in prev tranche for Work report: {wr_hash}")
            return None

        elif validator_index in false_votes:
            logger.info(f"already false judgment given in prev tranche for Work report: {wr_hash}")
            return None

        else:
            # 2. -------------- Guarantee refine check -------------------
            block = Block.load(header_hash=header_hash, db=settings.main_db)
            guarantee_found = False

            guarantee_ext = block.extrinsic.guarantees
            for guarantee in guarantee_ext:
                if guarantee.report.hash() == wr_hash:
                    guarantee_found = True
                    break

            if guarantee_found:
                return U8(1)

            else:
                wr = await cls.fetch_report(wr_hash=wr_hash)
                validity = await Audit.refine(wr=wr)
                return validity

    @classmethod
    async def block_audited(cls, tranche: Tranche, block: Block, new_wrs: WorkReports) -> bool |  None:
        """
        block B may be considered audited, a condition denoted U, when all
        the work-reports which were made available are considered audited.
        """
        from jam.storage.tranche_audit_store import tranche_store, CoreReport

        header_hash = tranche.header_hash

        # ----------------- list of unaudited reports ------------
        unaudited_list = TypedVector[WorkReport]([])

        # ----------------- list of reports is audited -----------
        audited_wr_list = await tranche_store.get_audited_list(tranche=tranche)

        # ----------------- final audit check --------------------
        for wr in audited_wr_list:
            if wr != Null:
                wr_hash = wr.work_report.unwrap().hash()
                if wr_hash not in new_wrs:
                    unaudited_list.append(wr)

        if len(unaudited_list) == 0:
            logger.info(
                f"Block Audited 🔍 from audit engine",
                header_hash=header_hash.hex(),
                block_slot=block.header.slot,
                tranche=tranche,
            )
            return True
        else:
            logger.info("Found a report which is not audited, so block is unaudited, banned, chain revert logic")
            # Here we come on reverting
            cls.unaudited_revert(block=block)

    @classmethod
    def unaudited_revert(cls, block: Block):
        """  """
        from jam.settings import settings
        from jam.state.state import State, state
        header_hash = block.header.hash()

        States = State()

        # as soon as new slot began we start auditing process
        cache_update = State.load(header_hash=header_hash)

        # delete all cache and remove all it from thr DB and tries
        States.revert(header_hash=header_hash)
        ...

    @staticmethod
    async def is_tranche(
         block: Block,
         curr_tranche: Tranche,
         prev_tranche_state: TrancheState,
    ) -> TypedVector[SubsequentTrancheEvidence]:
        """
        Function to check whether the block is tranche will be continued or not.
        Builds new list to audit and corresponding no shows and Dispute.

        Args:
            block: Block to be audited
            curr_tranche: Tranche in which the block is currently in
            prev_tranche_state: last tranche state

        Returns:
            List of SubsequentTrancheEvidence
        """
        from jam.storage.tranche_audit_store import tranche_store
        from jam.audit.audit import Audit
        from jam.settings import settings

        audit = Audit()

        header_hash = curr_tranche.header_hash
        tranche_index = curr_tranche.tranche_index
        entropy_source = BandersnatchVrfSignature(block.header.entropy_source)
        bandersnatch_private = settings.bandersnatch_private

        # ---------- Calculate SubsequentTrancheEvidence, UNAUDITED list for this Tranche ----------
        updated_unaudited_list = OptionalReports([])
        subsequent_evidence = TypedVector[SubsequentTrancheEvidence]([])

        # ---------------------------- GET UNAUDITED LIST (q) FROM LAST TRANCHE and iterate----------
        prev_unaudited_reports = prev_tranche_state.unaudited_list

        for core_index, report in enumerate(prev_unaudited_reports):

            wr = report.unwrap()

            if wr == Null:
                updated_unaudited_list.append(OptionalReport(Null))

            else:
                wr_hash = wr.hash()

                if wr_hash in prev_tranche_state.records:

                    # ------------------------- WORK REPORT RECORDS FOR AUDITING  ------------------
                    audit_record = prev_tranche_state.records[wr_hash] # test here what if get no records found there
                    if audit_record is None and audit_record == AuditRecord.empty():
                        logger.error(f"No Audit Records exits for the report {wr_hash} in tranche {curr_tranche}")
                    else:
                        announces = audit_record.announces
                        true_votes = audit_record.true_votes
                        false_votes = audit_record.false_votes
                        no_shows = audit_record.no_shows

                        # ----------Checking Report audited and Next tranche report to process handling process ----------
                        if len(false_votes) == 0:
                            if len(no_shows) == 0:
                                if tranche_index > TrancheIndex(0):
                                    if len(announces) < len(true_votes):
                                        updated_unaudited_list.append(OptionalReport(Null))
                                        core_report = CoreReportHash(
                                            core_index=CoreIndex(core_index),
                                            report_hash=wr_hash
                                        )
                                        await tranche_store.add_to_audited_list(tranche=curr_tranche, c_w=core_report)
                                    else:
                                        logger.error(
                                            "got report which has announcements > true_votes"
                                        )
                                else:
                                    logger.error(
                                        "is_tranche function run for < Tranche = 0"
                                    )

                            else:
                                wr_no_shows = TypedVector[NoShow]([])

                                updated_unaudited_list.append(OptionalReport(wr))

                                bandersnatch_sign = audit.vrf_signature_bandersnatch(
                                    entropy_source=entropy_source,
                                    bandersnatch_key=bandersnatch_private,
                                    tranche=curr_tranche,
                                    w_r=wr
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
                        else:
                            logger.erro("Wrong work report read")
                else:
                    logger.error(
                        f"Work report exists in the unaudited list for tranche {curr_tranche}, "
                        "but it was not found in the audit records."
                    )

        await tranche_store.update_unaudited_list(
            tranche=curr_tranche,
            unaudited_reports=updated_unaudited_list
        )

        return subsequent_evidence

    @staticmethod
    async def dispute_ext(block: Block, tranche : Tranche) -> DisputesExtrinsic:
        """ here we build while dispute extrinsic """
        from jam.storage.tranche_audit_store import tranche_store
        from jam.state.state import state
        # TODO : Work Report Age
        # TODO : Error handling
        # TODO : Does need to wrap up into Type before adding into verdict, culprit and fault , check every where in this function

        # -------------------- Fetching State for dispute ext. calculate --------------------
        state = tranche_store.get_state(tranche=tranche)

        init_tranche = Tranche(
            tranche_index=TrancheIndex(0),
            header_hash=tranche.header_hash
        )

        init_state = tranche_store.get_state(tranche=init_tranche)
        unaudited_reports = init_state.unaudited_list

        # ------------------------ Empty dispute extrinsic -------------------
        verdicts = Verdicts([])
        culprits = Culprits([])
        faults = Faults([])

        # ------------------------ Build Dispute Extrinsic -------------------
        for core_index, report in enumerate(unaudited_reports):
            wr = report.unwrap()
            if wr != Null:
                wr_hash = wr.hash()
                audit_record = state.records[wr_hash]  # test here what if get no records found there
                if audit_record is None and audit_record == AuditRecord.empty():
                    logger.error(f"No Audit Records exits for the report {wr_hash} in tranche {tranche}")
                else:
                    announces = audit_record.announces
                    true_votes = audit_record.true_votes
                    false_votes = audit_record.false_votes

                    # ------------ Calculate report slot ------------
                    report_slot = None
                    for guarantee in block.extrinsic.guarantees:
                        if guarantee.report.hash() == wr_hash:
                            report_slot = guarantee.slot

                    report_age = EpochIndex(math.floor(report_slot / EPOCH_LENGTH))

                    # bit error handling for report slot
                    current_epoch = EpochIndex(math.floor(state.tau / EPOCH_LENGTH))

                    valid_ages = (
                        [current_epoch, current_epoch]
                        if current_epoch == 0
                        else [current_epoch, current_epoch - 1]
                    )

                    if report_age not in valid_ages:
                        logger.error(f"Work Report {wr_hash} is too old. can't process")
                        continue

                    # -------------- sorted judgments (votes) --------------

                    t_votes = list(true_votes)
                    f_votes = list(false_votes)

                    t_sorted = sorted(t_votes, key=lambda x: x[1])
                    f_sorted = sorted(f_votes, key=lambda x: x[1])

                    # -------------- remove duplicate if exist ------------


                    # ------------E_v | E_f | E_c --------------

                    if len(true_votes) >= VALIDATORS_SUPER_MAJORITY:
                        if len(false_votes) >= 1:
                            core_report = CoreReportHash(
                                core_index=CoreIndex(core_index),
                                report_hash=WorkReportHash(wr_hash)
                            )
                            await tranche_store.add_to_audited_list(tranche=tranche, c_w=core_report)

                            judgments = JudgementVotes([])
                            for t in t_sorted[:VALIDATORS_SUPER_MAJORITY]:
                                judgment = Judgement(
                                    vote=Bool(True),
                                    index=t.validator_index,
                                    signature=t.ed25519_signature
                                )

                                judgments.append(Judgement=judgment)


                            verdict = Verdict(
                                target=wr_hash,
                                age=U32(report_age),
                                votes=judgments
                            )

                            verdicts.append(verdict)

                            for f in f_sorted[1:]:
                                fault = Fault(
                                    target=wr_hash,
                                    vote=Bool(False),
                                    key=f.ed25519_public,
                                    signature=f.ed25519_signature
                                )
                        else:
                            logger.error(
                                "Report doesn't have more then one fault, it should "
                                "have at least one false votes (for Fault E_f)"
                            )

                    elif len(false_votes) >= VALIDATORS_SUPER_MAJORITY:
                        if len(true_votes) >= 2:
                            core_report = CoreReportHash(
                                core_index=CoreIndex(core_index),
                                report_hash=WorkReportHash(wr_hash)
                            )

                            judgments = JudgementVotes([])
                            for f in f_sorted[:VALIDATORS_SUPER_MAJORITY]:
                                judgment = Judgement(
                                    vote=Bool(False),
                                    index=f.validator_index,
                                    signature=f.ed25519_signature
                                )

                                judgments.append(Judgement=judgment)

                            verdict = Verdict(
                                target=wr_hash,
                                age=U32(report_age),
                                votes=judgments
                            )

                            verdicts.append(verdict)

                            # E_c ==>> culprit : True votes
                            for t in t_sorted:
                                """
                                1. can import block using header_hash
                                2. passing block (now using)
                                """
                                guarantee_ext = block.extrinsic.guarantees
                                found_report = False
                                for guarantee in guarantee_ext:
                                    if guarantee.report.hash() == wr_hash:
                                        found_report = True
                                        # leans two valid entry in culprits sequence
                                        if len(guarantee.signatures) >= 2:
                                            for s in guarantee.signatures:
                                                culprit = Culprit(
                                                    target=wr_hash,
                                                    key=t.ed25519_public,
                                                    signature=s.signature
                                                )
                                                culprits.append(culprit)
                                        else:
                                            logger.error("Dont have enough guarantee to build Culprit extrinsic")
                                    else:
                                        continue

                                if not found_report:
                                    logger.error("Work report not found in the guarantee, means No Culprits")
                        else:
                            logger.error("Culprit count is less than required")

                    else:  # wonky
                        # TODO: add them in sorted order
                        judgments = JudgementVotes([])
                        for t in t_sorted[:VALIDATORS_WONKY]:
                            judgment = Judgement(
                                vote=Bool(True),
                                index=t.validator_index,
                                signature=t.ed25519_signature
                            )
                            judgments.append(Judgement=judgment)

                        for f in f_sorted[:(VALIDATORS_SUPER_MAJORITY - VALIDATORS_WONKY)]:
                            judgment = Judgement(
                                vote=Bool(False),
                                index=ValidatorIndex(f.validator_index),
                                signature=Ed25519Signature(f.ed25519_signature)
                            )
                            judgments.append(Judgement=judgment)

                        verdict = Verdict(
                            target=wr_hash,
                            age=U32(report_age),
                            votes=judgments
                        )
                        verdicts.append(verdict)

        # --------------- sorting Ev, Ec and Ev ---------------
        # TODO: doubt for Ev, hash to int sort or Core index sort
        verdicts.sort(key=lambda v: int.from_bytes(v.target))
        culprits.sort(key=lambda c : int.from_bytes(c.key))
        faults.sort(key=lambda fs: int.from_bytes(fs.key))

        dispute_ext = DisputesExtrinsic(
            verdicts= verdicts,
            culprits= culprits,
            faults= faults
        )

        # check are case like sorting, duplicate faults >= 1, culprits >= 2 and many more.....
        # Add extrinsic into extrinsic store (local)
        from jam.block.extrinsics.disputes import dpt_store
        dpt_store.store(ext=dispute_ext)

        return dispute_ext