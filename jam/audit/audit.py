from typing import List, Tuple

from tsrkit_types import structure, Null, TypedVector, Bytes, Uint, Option, U8, U32

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jam.audit.assembler import Assembler
from jam.block import Block
from jam.network.utils.shards import get_si, get_vi
from jam.state.state import State
from jam.types.protocol.core import CoreIndex, TimeSlot, ValidatorIndex
from jam.ring_vrf.curve.specs.bandersnatch import (
    BandersnatchPoint,
    Bandersnatch_TE_Curve,
)
from jam.types.work.report import WorkReport
from jam.utils.constants import (
    CURRENT_TIME,
    SLOT_PERIOD,
    AUDIT_PERIOD,
    SIGNING_CONTEXTS,
    VALIDATOR_COUNT, CORE_COUNT, UNAVAILABLE_WORK_EXPIRY,
)
from jam.ring_vrf.vrf import VRF
from jam.utils.shuffle import shuffle
from jam.types.protocol.crypto import Hash, BandersnatchPublic
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.types import BandersnatchVrfSignature, Ed25519Signature
from jam.types.work.package import WorkPackage

from jam.block.header import Header

# from jam.types.state.rho import OptionalWorkReportState, Rho
from jam.logging import get_logger
from jam.audit.utils import sign_bandersnatch, audit_refine



from jam.types.audit.tranche import TrancheIndex

from tests.unit.safrole.data import validators
from jam.audit.utils import audit_refine

# Module-specifier logger
logger = get_logger("in_core")


class Utils:
    def __init__(self):
        self.vrf = VRF

    @staticmethod
    def fetch_auditable_reports(prior_state: State, block: Block) -> List[Option[WorkReport]]:
        """
        Equation: 17.1, 17.2
        Returns Auditable Report per Core

        Args:
            prior_state: Prior State to access pending work reports
            block: Block to access newly guaranteed work reports

        Returns:
            A sequence of optional auditable reports

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1e61001eb600?v=0.7.0
        """

        auditable_reports = list[Option[WorkReport]]([])
        pending_wrs = prior_state.rho
        new_wrs = block.extrinsic.guarantees

        wr_dict: dict[int, tuple[WorkReport, TimeSlot]] = {}
        for wrg in new_wrs:
            core_index = int(wrg.report.core_index)
            wr_dict[core_index] = wrg.report, wrg.slot

        # check for pending and new report for each core
        for i in range(CORE_COUNT):

            # if new report available
            if i in wr_dict:
                new_rep, ts = wr_dict[i]
                pending_rep = pending_wrs[i].unwrap()

                # if no pending report or new report is same as pending report
                if pending_rep == Null or pending_rep.report == new_rep:
                    auditable_reports.append(Option(new_rep))

                # TODO: Is this condition required?
                # if pending report's timeslot is way before than current report's timeslot
                elif pending_rep.timeout + UNAVAILABLE_WORK_EXPIRY <= ts:
                    auditable_reports.append(Option(new_rep))

                # pending report is still in pending state
                else:
                    auditable_reports.append(Option(Null))
            # if no new report available
            else:
                auditable_reports.append(Option(Null))

        return auditable_reports

    @staticmethod
    def vrf_signature_bandersnatch(
        entropy_source: BandersnatchVrfSignature,
        bandersnatch_key: BandersnatchPublic,
        tranche_index: U8,
        w_r: WorkReport = None,
    ) -> BandersnatchVrfSignature:
        """
        Equation: 17.3, 17.4
        This function create a random quantity to get entropy for shuffling.

        Args:
            entropy_source: Header's entropy-yielding vrf signature H_v
            bandersnatch_key: Validator(Node) bandersnatch key
            tranche_index: Current tranche index
            w_r: Work Report

        Return:
            Valid Bandersnatch Signature


        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1ec1001e0001?v=0.7.0
        """
        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)

        entropy_vrf_proof = vrf.proof_to_hash(
            BandersnatchPoint.encode_to_curve(entropy_source.encode())
        )[:32]
        context = SIGNING_CONTEXTS["audit"] + entropy_vrf_proof

        # if tranche_index is not Null and tranche_index > 0 and w_r is not Null:
        #     context += Bytes(Hash.blake2b(w_r.encode())) + Bytes(tranche_index)

        signature = sign_bandersnatch(key=bandersnatch_key, context=context)

        return signature

    @classmethod
    def verifiable_random_selection(
        cls,
        entropy_source: BandersnatchVrfSignature,
        bandersnatch_key: BandersnatchPublic,
        pre_audit_report: List[Option[WorkReport]],
    ) -> List[Tuple[CoreIndex, WorkReport]]:
        """
        Equation: 17.5, 17.6
        Here in this function we just take q(report_to_be_audit function above) , shuffled it and get initial 10 Work Reports assign to validator.

        Args:
            entropy_source:
            bandersnatch_key:
            pre_audit_report:

        Return:
            Random initial 10 not Null Work Reports

        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1e0a011e5601?v=0.7.0
        """

        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
        entropy = vrf.proof_to_hash(
            BandersnatchPoint.encode_to_curve(
                cls.vrf_signature_bandersnatch(
                    entropy_source=entropy_source,
                    bandersnatch_key=bandersnatch_key,
                    tranche_index=None,
                )
            )
        )[:32]

        # ---------------------------- mapping q's reports as tuple[CoreIndex, Option[WorkReport]] ---------------------
        core_report = list[Tuple[CoreIndex, Option[WorkReport]]]([])
        for c, w_r in enumerate(pre_audit_report):
            core_report.append((CoreIndex(c), w_r))

        # ---------------------------------- Array same as size of core_report and shuffle -----------------------------
        array_index = TypedVector[Uint[32]]([])
        for i in range(len(pre_audit_report)):
            array_index.append(Uint[32](i))

        # ------------------------- shuffle function that shuffle array based on entropy (for randomness) --------------
        shuffle_array = shuffle(entropy, array_index)

        # ---------------------------------------- updated shuffle auditing list ---------------------------------------
        lookup = dict(core_report)
        updated_array = [(CoreIndex(i), lookup[i]) for i in shuffle_array]

        # ------------------------------------------ take initial 10 reports -------------------------------------------
        # Eq. 17.5 : ao = {(c, w) | (c, w) E p... + 10, w != Phi }
        shuffle_not_null = list[Tuple[CoreIndex, WorkReport]]([(c, w) for (c, w) in updated_array if w is not Null][:4])

        return shuffle_not_null

    @staticmethod
    def get_tranche_index(slot: TimeSlot) -> TrancheIndex:
        """
        Equation: 17.8
        This function calculated the tranches based on the timeslot, Current time

        Args:
            Block's Timeslot

        Return:
            Current Tranches index

        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1e74011e8401?v=0.7.0
        """

        tranche_index =  TrancheIndex((CURRENT_TIME() - (SLOT_PERIOD * int(slot))) // AUDIT_PERIOD)
        return tranche_index

    @staticmethod
    def validator_announcement_statement(
        assign_report: List[Tuple[CoreIndex, WorkReport]], header: Header, tranche: U8
    ) -> Ed25519Signature:
        """
        Equations: 17.9, 17.10, 17.11
        This function create Announcement Statement (Valid Ed25519 Signature) is published and distributed to all other Validators Signature.

        Args:
            assign_report: Assigned Reports to the validator
            header: latest Block's Header
            tranche: Current tranche index

        Returns:
            valid Ed25519 Signature

        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1e9e011eec01?v=0.7.0
        """

        from jam.settings import settings
        from jam.network.node import node

        signing_context = Bytes(SIGNING_CONTEXTS["announce"])

        header_hash = Bytes(Hash.blake2b(header.encode()))

        set_value: set[Bytes] = set()

        for c, r in assign_report:
            report_encode = Bytes(c.encode() + Hash.blake2b(r.encode()))
            set_value.add(report_encode)

        set_encode = Bytes()

        for item in set_value:
            set_encode = item.encode() + set_encode

        message = signing_context + Bytes(tranche) + set_encode + header_hash

        ed25519_pvt = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private)
        signature = ed25519_pvt.sign(message)

        return Ed25519Signature(signature)

    @staticmethod
    async def refine(wr: WorkReport) -> bool:
        """
        Equation: 17.17
        Rebuild bundle for given work report, refine it and compare reports

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1f2f011f6c01?v=0.7.0
        Args:
            wr: Work Report
        Returns:
            Validation Result (Bool)
        """

        wr_hash = Hash.blake2b(wr.encode())

        from jam.incore import Processor

        assembler = Assembler()
        processor = Processor()

        try:
            logger.debug("Recompiling bundle...", wr_hash=wr_hash.hex())
            bundle = await assembler.assemble(wr)

            logger.debug("Reprocessing bundle...", wr_hash=wr_hash.hex())
            new_wr, new_wr_hash = processor.process_bundle(wr.core_index, bundle, wr.segment_root_lookup, False)

            logger.info("✒️ Audited report successfully!", wr_hash=wr_hash.hex(), is_valid=(wr_hash == new_wr_hash))
            assert wr_hash == new_wr_hash

            return True

        except Exception as NO_REFINE:
            logger.error(
                "Auditing failed..",
                err=str(NO_REFINE),
                err_type=type(NO_REFINE).__name__,
                wr_hash=wr_hash.hex()
            )

            return False

    @staticmethod
    def judgment_signature(wr: WorkReport, refine: bool) -> Bytes[96]:
        """
        Equations: 17.18
        This function just build the ed25519 signature(Judgment Signature) for the particular work report.

        Args:
            wr: Work Report
            refine: Boolean value (True/False)

        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1f6f011f9801?v=0.7.0

        """
        from jam.network.node import node
        from jam.settings import settings

        if refine:
            message = SIGNING_CONTEXTS["valid"] + Hash.blake2b(wr.encode())
        else:
            message = SIGNING_CONTEXTS["invalid"] + Hash.blake2b(wr.encode())


        ed25519_pvt = Ed25519PrivateKey.from_private_bytes(settings.ed25519_private)
        signature = ed25519_pvt.sign(message)

        return Ed25519Signature(signature)

    def audited_report(
        self, pre_audit: List[Option[WorkReport]]
    ) -> TypedVector[Option[WorkReport]]:
        """
        Equation: 17.19, 17.20
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1fa9011fd301?v=0.7.0
        """

        # condition 1 => on that core all the judgment should be true and A_n(r) ⊂ J_T(r
        # condition 2 => if in tranche all the judgment of the validator should be > 2/3
