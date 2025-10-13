import math
from tsrkit_types import U32, Uint, U8, Null, TypedVector, Bool
from jam.block.extrinsics.disputes import DisputesExtrinsic, Verdicts, Culprits, Faults
from jam.block.block import Block
from jam.types.work.report import WorkReportHash, WorkReport, WorkReports
from jam.types.audit.audit_tranche import TrancheIndex, Tranche, OptionalReports, OptionalReport, TrancheState, CoreReport, AuditRecord
from jam.types.protocol.crypto import BandersnatchVrfSignature, Ed25519Signature
from jam.types.protocol.core import CoreIndex, EpochIndex, ValidatorIndex
from jam.network.protocols.ce_144 import NoShow, SubsequentTrancheEvidence
from jam.utils.constants import EPOCH_LENGTH, VALIDATORS_SUPER_MAJORITY, VALIDATORS_WONKY
from jam.block.extrinsics.disputes import Verdict, Culprit, Fault, JudgementVotes, Judgement
from jam.log_setup import network_logger

logger = network_logger


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
    async def block_audited(
        cls, tranche: Tranche,
        block: Block,
        newly_avail_wrs: WorkReports
    ) -> bool |  None:
        """
        block B may be considered audited, a condition denoted U, when all
        the work-reports which were made available are considered audited.
        """
        from jam.storage.tranche_audit_store import tranche_store

        header_hash = tranche.header_hash

        # ----------------- list of unaudited reports ------------
        unaudited_list = TypedVector[CoreReport]([])

        # ----------------- list of reports is audited -----------
        audited_wr_list = await tranche_store.get_audited_list(tranche=tranche)

        # ----------------- final audit check --------------------
        for c_r in audited_wr_list:
            wr = c_r.work_report
            if wr not in newly_avail_wrs:
                unaudited_list.append(c_r)

        if len(unaudited_list) == 0:
            logger.info(
                f"Block Audited 🔍 from audit engine",
                header_hash=header_hash.hex(),
                block_slot=block.header.slot,
                tranche=tranche,
            )
            return True
        else:
            logger.debug(
                "Found a report which is not audited, so block is unaudited, banned, chain revert logic"
            )
            return False


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

                        # ---------- Checking Report audited and Next tranche report to process handling process --------
                        if len(false_votes) == 0:
                            if len(no_shows) == 0:
                                if tranche_index == TrancheIndex(1):
                                    if len(announces) <= len(true_votes):
                                        updated_unaudited_list.append(OptionalReport(Null))
                                        core_wr = CoreReport(
                                            core_index=CoreIndex(core_index),
                                            work_report=wr
                                        )
                                        await tranche_store.add_to_audited_list(tranche=curr_tranche, c_r=core_wr)
                                    else:
                                        logger.error(
                                            "got report which has announcements > true_votes"
                                        )
                                else:
                                    if len(announces) < len(true_votes):
                                        updated_unaudited_list.append(OptionalReport(Null))
                                        core_wr = CoreReport(
                                            core_index=CoreIndex(core_index),
                                            work_report=wr
                                        )
                                        await tranche_store.add_to_audited_list(tranche=curr_tranche, c_r=core_wr)
                                    else:
                                        logger.error(
                                            "got report which has announcements > true_votes"
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
                                    if no_show.validator_index not in wr_no_shows:
                                        wr_no_shows.append(no_show)

                                subsequent_evidence.append(
                                    SubsequentTrancheEvidence(
                                        bandersnatch_signature=BandersnatchVrfSignature(bandersnatch_sign),
                                        no_shows=wr_no_shows
                                    )
                                )
                        else:
                            logger.info(
                                "This report has false judgment will go for dispute."
                            )

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
        from jam.settings import settings

        # -------------------- Fetching State for dispute ext. calculate --------------------
        state = await tranche_store.get_state(tranche=tranche)

        init_tranche = Tranche(
            tranche_index=TrancheIndex(0),
            header_hash=tranche.header_hash
        )

        init_state = await tranche_store.get_state(tranche=init_tranche)
        unaudited_reports = init_state.unaudited_list

        # ------------------------ Empty dispute extrinsic -------------------
        verdicts = Verdicts([])
        culprits = Culprits([])
        faults = Faults([])

        # ------------------------ Build Dispute Extrinsic -------------------
        found_dispute = False
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

                    if len(false_votes) > 0:
                        found_dispute = True

                        # ------------ Calculate report slot ------------
                        founded = False
                        report_slot = None
                        need_block = Block.load(header_hash=block.header.hash(), db=settings.main_db)
                        process_block = None

                        while not founded and need_block is not None:
                            process_block = need_block

                            for guarantee in process_block.extrinsic.guarantees:
                                if guarantee.report.hash() == wr_hash:
                                    report_slot = guarantee.slot
                                    founded = True
                                    break

                            if not founded:
                                parent_hash = process_block.header.parent
                                need_block = Block.load(header_hash=parent_hash, db=settings.main_db)

                        if report_slot is None:
                            raise ValueError(f"Report {wr_hash.hex()} not found in blocks history.")

                        report_age = EpochIndex(math.floor(report_slot / EPOCH_LENGTH))
                        # bit error handling for report slot
                        from jam.state.state import state
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

                        t_sorted = sorted(t_votes, key=lambda x: x.validator_index)
                        f_sorted = sorted(f_votes, key=lambda x: x.validator_index)

                        # ------------E_v | E_f | E_c --------------
                        if len(true_votes) >= VALIDATORS_SUPER_MAJORITY:
                            if len(false_votes) >= 1:
                                core_wr = CoreReport(
                                    core_index=CoreIndex(core_index),
                                    work_report=wr
                                )
                                await tranche_store.add_to_audited_list(tranche=tranche, c_r=core_wr)

                                judgments = TypedVector[Judgement]([])
                                for t in t_sorted[:VALIDATORS_SUPER_MAJORITY]:

                                    judgment = Judgement(
                                        vote=Bool(True)._value,
                                        index=t.validator_index,
                                        signature=t.ed25519_signature
                                    )

                                    judgments.append(judgment)

                                verdict = Verdict(
                                    target=wr_hash,
                                    age=U32(report_age),
                                    votes=JudgementVotes(judgments)
                                )

                                verdicts.append(verdict)

                                for f in f_sorted:
                                    fault = Fault(
                                        target=wr_hash,
                                        vote=Bool(False)._value,
                                        key=f.ed25519_public,
                                        signature=f.ed25519_signature
                                    )

                                    faults.append(fault)

                            else:
                                logger.error(
                                    "Report doesn't have more then one fault, it should "
                                    "have at least one false votes (for Fault E_f)"
                                )

                        elif len(false_votes) >= VALIDATORS_SUPER_MAJORITY:

                            judgments = TypedVector[Judgement]([])
                            for f in f_sorted[:VALIDATORS_SUPER_MAJORITY]:
                                judgment = Judgement(
                                    vote=Bool(False)._value,
                                    index=f.validator_index,
                                    signature=f.ed25519_signature
                                )

                                judgments.append(judgment)

                            verdict = Verdict(
                                target=wr_hash,
                                age=U32(report_age),
                                votes=JudgementVotes(judgments)
                            )
                            verdicts.append(verdict)

                            # E_c ==>> culprit : True votes          # more need to check it to get report
                            for t in t_sorted:

                                guarantee_ext = process_block.extrinsic.guarantees
                                for guarantee in guarantee_ext:
                                    if guarantee.report.hash() == wr_hash:
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
                                            raise
                                    else:
                                        continue

                        else:  # wonky
                            # TODO: add them in sorted order
                            judgments = JudgementVotes([])
                            for t in t_sorted[:VALIDATORS_WONKY]:
                                judgment = Judgement(
                                    vote=Bool(True)._value,
                                    index=t.validator_index,
                                    signature=t.ed25519_signature
                                )
                                judgments.append(Judgement=judgment)

                            for f in f_sorted[:(VALIDATORS_SUPER_MAJORITY - VALIDATORS_WONKY)]:
                                judgment = Judgement(
                                    vote=Bool(False)._value,
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

                    else:
                        logger.info(
                            "Work report has not any negative judgment. So no dispute happen "
                        )
                        continue

        if not found_dispute:
            logger.info(
                "There is not dispute in this block",
                header_hash=block.header.hash(),
                block_slot=block.header.slot,
            )

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