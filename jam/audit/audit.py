from jam.models.state.rho import WorkReportState, OptionalWorkReportState
from tsrkit_types import Null, TypedVector, Bytes, Uint, U8
from dot_ring import IETF_VRF, Bandersnatch
from jam.models.protocol.core import CoreIndex
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

from jam.models.protocol.crypto import HeaderHash
from jam.models import BandersnatchVrfSignature, Ed25519Signature, WorkReportHash
from jam.models.audit.audit_tranche import (
    Tranche,
    OptionalReports,
    TrancheIndex,
    OptionalReport,
    CoreOptionalReport,
    CoreReport,
)
from jam.models.work.report import WorkReport
from jam.utils.constants import VALIDATOR_COUNT, AUDIT_BIAS_FACTOR, AUDIT_REPORT_ASSIGNED
from jam.log_setup import logger


class Audit:
    @staticmethod
    def auditable_reports(
        prior_state: TypedVector[OptionalWorkReportState], newly_rep: TypedVector[WorkReport]
    ) -> OptionalReports:
        """
        Equation: 17.1, 17.2
        Define the sequence of work-reports which we may be required to audit as q = [ |R ?]c,
        a sequence of length equal to the number of core.

        Args:
            prior_state: p (rho) block prior state
            newly_rep: Work Report pending which has just become available.

        Source :https://graypaper.fluffylabs.dev/#/ab2cdbd/1e60001ea900?v=0.7.2
        """

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
        w_r: WorkReport | None = None,
    ) -> BandersnatchVrfSignature:
        """
        Equation: 17.3, 17.4
        This function create a random quantity to get entropy for shuffling.

        Args:
            tranche: Current tranche
            bandersnatch_key: Validator(Node) bandersnatch key
            entropy_source: Header's entropy-yielding vrf signature H_v
            w_r: Work Report

        Return:
            Valid Bandersnatch Signature

        Source: https://graypaper.fluffylabs.dev/#/ab2cdbd/1eb5001ef400?v=0.7.2
        """

        tranche_index = tranche.tranche_index

        # Use dot_ring for VRF output extraction
        entropy_ring_proof = IETF_VRF[Bandersnatch].from_bytes(entropy_source.encode())
        entropy_vrf_proof = BandersnatchVrfSignature(
            entropy_ring_proof.proof_to_hash(entropy_ring_proof.output_point)[:32]
        )

        context = X.AUDIT.value + entropy_vrf_proof

        if tranche_index != TrancheIndex(0):
            context += w_r.hash() + tranche_index.encode()

        ietf_proof = IETF_VRF[Bandersnatch].prove(
            context,
            bandersnatch_key,
            b"",
        )

        return BandersnatchVrfSignature(ietf_proof.to_bytes())

    @classmethod
    def verifiable_random_selection(
        cls,
        tranche: Tranche,
        bandersnatch_key: Bytes[32],
        unaudited_report: OptionalReports,
        entropy_source: BandersnatchVrfSignature,
    ) -> TypedVector[CoreReport]:
        """
        Equation: 17.5, 17.6
        Implements the shuffling procedure defined in Gray Paper eq. 17.5–17.6 to randomly order the auditor’s work-report
        queue using the seed S₀, and then selects the first 10 work reports for that validator.

        Args:
            entropy_source: Header's entropy-yielding vrf signature H_v
            bandersnatch_key: Validator(Node) bandersnatch key
            unaudited_report: q (work-reports which we may be required to audit)
            tranche: Current tranche index

        Return:
           A list containing the first 10 work reports extracted from the permuted sequence — these are the assigned work reports the validator must audit.

        Source: https://graypaper.fluffylabs.dev/#/ab2cdbd/1efe001e4a01?v=0.7.2
        """

        # Extract VRF output using dot_ring
        vrf_sig = cls.vrf_signature_bandersnatch(
            entropy_source=entropy_source,
            bandersnatch_key=bandersnatch_key,
            tranche=tranche,
            w_r=None,
        )
        ietf_proof = IETF_VRF[Bandersnatch].from_bytes(vrf_sig)
        entropy = ietf_proof.proof_to_hash(ietf_proof.output_point)[:32]

        # ---------------------------- mapping q's reports as tuple[CoreIndex, Option[WorkReport]] ---------------------
        core_report = TypedVector[CoreOptionalReport]([])
        for c, wr in enumerate(unaudited_report):
            value = CoreOptionalReport(core_index=CoreIndex(c), work_report=wr)
            core_report.append(value)

        # ---------------------------------- Array same as size of core_report and shuffle -----------------------------
        index_array = TypedVector[Uint[32]]([])
        for i in range(len(unaudited_report)):
            index_array.append(Uint[32](i))

        # ------------------------- shuffle function that shuffle array based on entropy (for randomness) --------------
        shuffle_array = shuffle(entropy, index_array)

        # ---------------------------------------- updated shuffle auditing list ---------------------------------------
        lookup = {cr.core_index: cr for cr in core_report}
        updated_array = [lookup[CoreIndex(i)] for i in shuffle_array]

        # ------------------------------------------ take initial 10 reports -------------------------------------------
        # Eq. 17.5 : ao = {(c, w) | (c, w) E p... + 10, w != Phi }
        shuffle_not_null = TypedVector[CoreReport](
            [
                CoreReport(core_index=c_r.core_index, work_report=c_r.work_report.unwrap())
                for c_r in updated_array
                if c_r.work_report.unwrap() is not Null
            ][:AUDIT_REPORT_ASSIGNED]
        )

        return shuffle_not_null

    @staticmethod
    def tranche_index(header: Header) -> TrancheIndex:
        """
        Equation: 17.7
        This function calculated the tranches based on the timeslot, Current time.

        Args:
            Block's Timeslot

        Return:
            Current Tranche index

        Source: https://graypaper.fluffylabs.dev/#/ab2cdbd/1e5c011e5c01?v=0.7.2
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
        Equations: 17.8, 17.9, 17.10
        For tranche n, the function encodes all announcement pairs (r, c) into xₙ, adds the validator ID v,
        evidence sₙ, and the `$jam_announce` tag, signs the bundle, and broadcasts the announcement to all validators.

        Args:
            tranche: Current tranche
            header_hash: latest Block's Header
            assign_report: Assigned Reports to the validator

        Returns:
            valid Ed25519 Signature

        Source: https://graypaper.fluffylabs.dev/#/ab2cdbd/1e8b011ee501?v=0.7.2
        """
        from jam.settings import settings

        tranche_index = tranche.tranche_index

        signing_context = Bytes(X.ANNOUNCE.value)

        set_value: set[Bytes] = set()

        for c_r in assign_report:
            report_encode = Bytes(c_r.core_index.encode() + c_r.work_report.hash())
            set_value.add(report_encode)

        set_encode = Bytes(b"")

        for item in set_value:
            set_encode = item + set_encode

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
        aₙ is the set of validators required to audit tranche n, recomputed each round using a VRF over the no-show validators.

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

            if rep is not Null:
                random_quantity = cls.vrf_signature_bandersnatch(
                    bandersnatch_key=settings.bandersnatch_private,
                    entropy_source=entropy,
                    tranche=tranche,
                    w_r=rep,
                )

                # HERE WE CHECK VRF CONDITION - extract VRF output using dot_ring
                rand_proof = IETF_VRF[Bandersnatch].from_bytes(random_quantity)
                vrf_out = rand_proof.proof_to_hash(rand_proof.output_point)[:32]
                vrf_check = (VALIDATOR_COUNT / (256 * AUDIT_BIAS_FACTOR)) * vrf_out[1:]

                # NO-JUDGMENT FOR THAT WORK REPORT
                prev_tranche_index = tranche_index - TrancheIndex(1)

                prev_tranche = Tranche(tranche_index=prev_tranche_index, header_hash=header_hash)

                wr_hash = rep.hash()

                state = await tranche_store.get_state(tranche=prev_tranche)

                records = state.records.get(wr_hash)

                # Count of no-judgment and negative judgment for that work_report
                m_n = len(records.announces) - len(records.true_votes)

                if vrf_check < m_n:
                    assigned_report = CoreReport(
                        core_index=CoreIndex(rep.core_index), work_report=rep
                    )

                    assigned_wrs.append(assigned_report)

        return assigned_wrs

    @staticmethod
    async def refine(wr: WorkReport) -> Uint:
        """
        Equation: 17.16
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

            return U8(1)

        except Exception as NO_REFINE:
            logger.error(
                "Auditing failed..",
                err=str(NO_REFINE),
                err_type=type(NO_REFINE).__name__,
                wr_hash=wr_hash.hex(),
            )

            return U8(0)

    @staticmethod
    def judgment_signature(wr_hash: WorkReportHash, validity: Uint[8]) -> Ed25519Signature:
        """
        Equations: 17.17
        This function just build the ed25519 signature(Judgment Signature) for the particular work report.

        Args:
            wr_hash: Work Report Hash
            validity: Boolean value (True/False)

        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1f6f011f9801?v=0.7.0

        """
        from jam.settings import settings

        if validity == Uint[8](1):
            message = X.VALID.value + wr_hash.encode()
        else:
            message = X.INVALID.value + wr_hash.encode()

        ed25519_pvt = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private)
        signature = ed25519_pvt.sign(message)

        return Ed25519Signature(signature)
