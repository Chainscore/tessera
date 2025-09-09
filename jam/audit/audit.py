from jam.logging import get_logger
from jam.types.state.rho import WorkReportState, OptionalWorkReportState
from tsrkit_types import Null, TypedVector, Bytes, Uint
from py_ark_vrf import prove_ietf, vrf_output
from jam.types.protocol.core import CoreIndex
from jam.block.header.header import Header
from jam.utils.constants import (
    CURRENT_TIME,
    SLOT_PERIOD,
    AUDIT_PERIOD,
    X,
)
from jam.utils.shuffle import shuffle
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jam.audit.assembler import Assembler

from jam.types.protocol.crypto import HeaderHash
from jam.types import BandersnatchVrfSignature, Ed25519Signature, WorkReportHash
from jam.types.audit.audit_tranche import (
    TrancheIndex,
    Tranche,
    OptionalReports,
    TrancheIndex,
    OptionalReport,
    CoreReport,
)
from jam.types.work.report import WorkReport
from jam.utils.constants import VALIDATOR_COUNT, AUDIT_BIAS_FACTOR


# Module-specifier logger
logger = get_logger("auditor")


class Audit:

    @staticmethod
    def auditable_reports(
        prior_state: TypedVector[OptionalWorkReportState], newly_rep: OptionalReports
    ) -> OptionalReports:
        """ """
        auditable_reports = OptionalReports([])

        for r in prior_state:
            report_state: (WorkReportState | Null) = r.unwrap()
            if isinstance(report_state, WorkReportState) and report_state.report in newly_rep:
                auditable_reports.append(OptionalReport(report_state.report))
            else:
                auditable_reports.append(OptionalReport(Null))

        return auditable_reports

    @staticmethod
    def vrf_signature_bandersnatch(
        tranche: Tranche,
        bandersnatch_key: Bytes[32],
        entropy_source: BandersnatchVrfSignature,
        w_r: WorkReport = None,
    ) -> BandersnatchVrfSignature:
        """
        Equation: 17.3, 17.4
        This function create a random quantity to get entropy for shuffling.

        Args:
            entropy_source: Header's entropy-yielding vrf signature H_v
            bandersnatch_key: Validator(Node) bandersnatch key
            tranche: Current tranche
            w_r: Work Report

        Return:
            Valid Bandersnatch Signature


        Source: https://graypaper.fluffylabs.dev/#/1c979cb/1eb2001ed800?v=0.7.1
        """
        tranche_index = tranche.tranche_index

        entropy_vrf_proof = BandersnatchVrfSignature(vrf_output(entropy_source.encode()))

        context = X.AUDIT.value + entropy_vrf_proof

        if tranche_index != TrancheIndex(0):
            context += w_r.hash().encode() + tranche_index.encode()

        signature = prove_ietf(bandersnatch_key, context, b"")

        return BandersnatchVrfSignature(signature)

    @classmethod
    def verifiable_random_selection(
        cls,
        entropy_source: BandersnatchVrfSignature,
        bandersnatch_key: Bytes[32],
        unaudited_report: OptionalReports,
        tranche: Tranche,
    ) -> TypedVector[CoreReport]:
        """
        Equation: 17.5, 17.6
        Here in this function we just take q(report_to_be_audit function above) , shuffled it and get initial 10 Work Reports assign to validator.

        Args:
            entropy_source: Header's entropy-yielding vrf signature H_v
            bandersnatch_key: Validator(Node) bandersnatch key
            unaudited_report: q (work-reports which we may be required to audit)
            tranche: Current tranche index

        Return:
            Random initial 10 not Null Work Reports

        Source: https://graypaper.fluffylabs.dev/#/1c979cb/1efb001e4701?v=0.7.1
        """

        entropy = vrf_output(
            cls.vrf_signature_bandersnatch(
                entropy_source=entropy_source,
                bandersnatch_key=bandersnatch_key,
                tranche=tranche,
                w_r=None,
            )
        )

        # ---------------------------- mapping q's reports as tuple[CoreIndex, Option[WorkReport]] ---------------------
        core_report = TypedVector[CoreReport]([])
        for c, w_r in enumerate(unaudited_report):
            value = CoreReport(core_index=CoreIndex(c), work_report=OptionalReport(w_r))
            core_report.append(value)

        # ---------------------------------- Array same as size of core_report and shuffle -----------------------------
        array_index = TypedVector[Uint[32]]([])
        for i in range(len(unaudited_report)):
            array_index.append(Uint[32](i))

        # ------------------------- shuffle function that shuffle array based on entropy (for randomness) --------------
        shuffle_array = shuffle(entropy, array_index)

        # ---------------------------------------- updated shuffle auditing list ---------------------------------------
        # lookup = dict(core_report)
        # updated_array = [(CoreIndex(i), lookup[i]) for i in shuffle_array]
        lookup = {cr.core_index: cr for cr in core_report}
        updated_array = [lookup[CoreIndex(int(i))] for i in shuffle_array]

        # ------------------------------------------ take initial 10 reports -------------------------------------------
        # Eq. 17.5 : ao = {(c, w) | (c, w) E p... + 10, w != Phi }
        shuffle_not_null = TypedVector[CoreReport](
            [c_r for c_r in updated_array if c_r.work_report != Null][:2]
        )

        return

    @staticmethod
    def tranche_index(header: Header) -> TrancheIndex:
        """
        Equation: 17.7
        This function calculated the tranches based on the timeslot, Current time

        Args:
            Block's Timeslot

        Return:
            Current Tranches index

        Source: https://graypaper.fluffylabs.dev/#/1c979cb/1e51011e6501?v=0.7.1
        """

        tranche_index = TrancheIndex(
            (CURRENT_TIME() - (SLOT_PERIOD * int(header.slot))) // AUDIT_PERIOD
        )
        return tranche_index

    @staticmethod
    def validator_announcement_statement(
        tranche: Tranche, header_hash: HeaderHash, assign_report: TypedVector[CoreReport]
    ) -> Ed25519Signature:
        """
        Equations: 17.9, 17.10, 17.11
        This function create Announcement Statement (Valid Ed25519 Signature) is published and distributed to all other Validators Signature.

        Args:
            assign_report: Assigned Reports to the validator
            header_hash: latest Block's Header
            tranche: Current tranche

        Returns:
            valid Ed25519 Signature

        Source: https://graypaper.fluffylabs.dev/#/1c979cb/1e7a011ec901?v=0.7.1
        """
        from jam.settings import settings

        tranche_index = tranche.tranche_index

        signing_context = Bytes(X.ANNOUNCE.value)

        set_value: set[Bytes] = set()

        for c_r in assign_report:
            report_encode = Bytes(c_r.core_index.encode() + c_r.work_report.hash().encode())
            set_value.add(report_encode)

        set_encode = Bytes()

        for item in set_value:
            set_encode = item.encode() + set_encode

        message = signing_context + Bytes(tranche_index) + set_encode + header_hash

        ed25519_pvt = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private)
        signature = ed25519_pvt.sign(message)

        return Ed25519Signature(signature)

    @classmethod
    async def vrf_tranche(
        cls,
        header_hash: HeaderHash,
        tranche: Tranche,
        entropy: BandersnatchVrfSignature,
        unaudited_wrs: OptionalReports,
    ) -> TypedVector[CoreReport]:
        """
        Equation: 17.14, 17.15
        This function define a_n beyond the initial tranche through a new vrf which acts upon the set of no-show validators (for n (tranche) > 0).

        Args:
            header_hash: Current Tranche Header hash
            tranche: Current Tranche
            entropy: Entropy source
            unaudited_wrs: List of Work Reports will audit (for this tranche)

        Return:
            Assigned report for

        Source: https://graypaper.fluffylabs.dev/#/1c979cb/1f3d001fb900?v=0.7.1
        """
        from jam.settings import settings
        from jam.storage.tranche_audit_store import tranche_store

        tranche_index = tranche.tranche_index

        # DEFINE EMPTY LIST
        assigned_wrs = TypedVector[CoreReport]([])

        for wr in unaudited_wrs:
            rep = wr.unwrap()
            if isinstance(rep, WorkReport):
                random_quantity = cls.vrf_signature_bandersnatch(
                    bandersnatch_key=settings.bandersnatch_private,
                    entropy_source=entropy,
                    tranche=tranche,
                    w_r=rep,
                )

                # HERE WE CHECK VRF CONDITION
                vrf_check = (VALIDATOR_COUNT / (256 * AUDIT_BIAS_FACTOR)) * vrf_output(
                    random_quantity
                )[1:]

                # NO-JUDGMENT FOR THAT WORK REPORT
                prev_tranche_index = tranche_index - TrancheIndex(1)

                prev_tranche = Tranche(tranche_index=prev_tranche_index, header_hash=header_hash)

                wr_hash = rep.hash()

                state = await tranche_store.get_state(tranche=prev_tranche)

                records = state.judgments.get(wr_hash)

                # Count of no-judgment and negative judgment for that work_report
                m_n = len(records.announces) - len(records.true_votes)

                if vrf_check < m_n:
                    assigned_report = CoreReport(core_index=rep.core_index, work_report=rep)

                    assigned_wrs.append(assigned_report)

        return assigned_wrs

    @staticmethod
    async def refine(wr: WorkReport) -> bool:
        """
        Equation: 17.17
        Rebuild bundle for given work report, refine it and compare reports

        Args:
            wr: Work Report

        Returns:
            Validation Result (Bool)

        Source: https://graypaper.fluffylabs.dev/#/1c979cb/1fde001f1b01?v=0.7.1
        """

        wr_hash = wr.hash()
        from jam.incore import Processor

        assembler = Assembler()
        processor = Processor()

        try:
            logger.debug("Recompiling bundle...", wr_hash=wr_hash.hex())
            bundle = await assembler.assemble(wr)

            logger.debug("Reprocessing bundle...", wr_hash=wr_hash.hex())
            new_wr, new_wr_hash = processor.process_bundle(
                wr.core_index, bundle, wr.segment_root_lookup, False
            )

            logger.info(
                "✒️ Audited report successfully!",
                wr_hash=wr_hash.hex(),
                is_valid=(wr_hash == new_wr_hash),
            )
            assert wr_hash == new_wr_hash

            return True

        except Exception as NO_REFINE:
            logger.error(
                "Auditing failed..",
                err=str(NO_REFINE),
                err_type=type(NO_REFINE).__name__,
                wr_hash=wr_hash.hex(),
            )

            return False

    @staticmethod
    def judgment_signature(wr: WorkReport, validity: Uint[8]) -> Bytes[96]:
        """
        Equations: 17.17
        This function just build the ed25519 signature(Judgment Signature) for the particular work report.

        Args:
            wr: Work Report
            validity: Boolean value (True/False)

        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1f6f011f9801?v=0.7.0

        """
        from jam.settings import settings

        wr_hash = wr.hash()
        if validity == Uint[8](1):
            message = X.VALID.value + wr_hash.encode()
        else:
            message = X.INVALID.value + wr_hash.encode()

        ed25519_pvt = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private)
        signature = ed25519_pvt.sign(message)

        return Ed25519Signature(signature)
