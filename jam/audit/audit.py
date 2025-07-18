from typing import List, Tuple

from tsrkit_types import structure,  Null, TypedVector, Bytes, Uint, Option, U8, Bool, Dictionary

# from jam.audit.vectors.reports import reports
from jam.types.protocol.core import CoreIndex, TimeSlot
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
from jam.types.work.report import WorkReport
from jam.utils.constants import CURRENT_TIME, SLOT_PERIOD, AUDIT_PERIOD, SIGNING_CONTEXTS
from jam.ring_vrf.vrf import VRF
from jam.utils.shuffle import shuffle
from jam.types.protocol.crypto import Hash, BandersnatchPublic, Ed25519Public
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.types import BandersnatchVrfSignature, Ed25519Signature
from jam.types.work.package import WorkPackage, WorkPackageBundle
from jam.types.work.report import WorkReportHash
from jam.work_package.processor import Processor

from jam.types.block.header import Header
from jam.types.state.rho import OptionalWorkReportState
from jam.logging import get_logger
from jam.audit.utils import signature_pvt

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jam.network.node import Node
from jam.types.work.manifest import Extrinsics

# Module-specifier logger
logger = get_logger("in_core")



class AuditingAndJudgement:

    node: Node
    def __init__(self, node: Node):
        self.vrf = VRF
        self.node = node

    @staticmethod
    def report_to_be_audit(pending_wrs: List[Option[WorkReport]], newly_avail_wrs: List[Option[WorkReport]]) -> List[Option[WorkReport]]:
        """
        This functions as a mapping of core index to a work-report pending which has just become available, or ∅ if no report became available on the core.

        Args:
            newly_avail_wrs: Reports just become available after assurances
            pending_wrs: Pending Work Reports (Rho)

        Returns:
            A sequence of length equal to the number of cores

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1e61001eb600?v=0.7.0
        """

        pre_audit_report : List[Option[WorkReport]]= []

        # for i, report in enumerate(pending_wrs):
        #     if report is not Null:
        #         if report in newly_avail_wrs:
        #             pre_audit_report.append(report["report"])
        #         else:
        #             pre_audit_report.append(Null)
        #     else:
        #         pre_audit_report.append(Null)
        #
        for i in range(len(pending_wrs)):
            value1 = pending_wrs[i]
            value2 = newly_avail_wrs[i]

            if value1 is Null:
                pre_audit_report.append(Null)
            else:
                if value1 == value2:
                    pre_audit_report.append(value1)
                else:
                    pre_audit_report.append(Null)

        return pre_audit_report

        # for i in range(len(pending_wrs)):
        #     value1 = pending_wrs[i]
        #     value2 = newly_avail_wrs[i]
        #
        #     if value1 is None:
        #         pre_audit_report.append(Null)
        #     else:
        #         if value1 == value2:
        #             pre_audit_report.append(value1)
        #         else:
        #             pre_audit_report.append(Null)


        return pre_audit_report

    @staticmethod
    def vrf_signature_bandersnatch(entropy_source: BandersnatchVrfSignature, bandersnatch_key: BandersnatchPublic, tranche_index: U8 = None, w_r: WorkReport = None ) -> Bytes[96]:
        """
        Equation: 17.3, 17.4
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1ec1001e0001?v=0.7.0
        """
        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)

        entropy_vrf_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(entropy_source.encode()))[:32]
        context = Bytes(SIGNING_CONTEXTS["audit"]) + entropy_vrf_proof

        # if tranche_index is not Null and tranche_index > 0 and w_r is not Null:
        #     random_quantity += Bytes(Hash.blake2b(w_r.encode())) + Bytes(tranche_index)

        signature = signature_pvt(key=bandersnatch_key, context=context)

        return signature

    def verifiable_random_selection(self, entropy_source: BandersnatchVrfSignature, bandersnatch_key: BandersnatchPublic, pre_audit_report: List[Option[WorkReport]]) -> List[Tuple[CoreIndex, WorkReport]]:
        """
        Equation: 17.5, 17.6
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1e0a011e5601?v=0.7.0
        """
        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
        entropy = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(self.vrf_signature_bandersnatch(entropy_source=entropy_source, bandersnatch_key=bandersnatch_key)))[:32]

        pre_audit_reports = pre_audit_report
        core_indexes = list[Tuple[CoreIndex, Option[WorkReport]]]([])
        for c, w_r in enumerate(pre_audit_reports):
            core_indexes.append((CoreIndex(c), w_r))

        # return core_indexes
        # ------------------------------------- audit size array and shuffle --------------------------------------------
        array_index = TypedVector[Uint[32]]([])
        for i in range(len(pre_audit_reports)):
            array_index.append(Uint[32](i))

        shuffle_array = shuffle(entropy, array_index)

        # ------------------------------------------ updated shuffle auditing list -------------------------------------
        lookup = dict(core_indexes)
        updated_array : List[tuple[core_indexes, Option[WorkReport]]] = [(CoreIndex(i), lookup[i]) for i in shuffle_array]

        # return updated_array
        # ------------------------------------------ take initial 10 values --------------------------------------------
        # Eq. 17.5 : ao = {(c, w) | (c, w) E p... + 10, w != Phi }
        shuffle_not_null  = [(c, w) for (c, w) in updated_array if w is not Null][:10]

        return shuffle_not_null

    @staticmethod
    def tranche_index(header_slot: TimeSlot) -> U8:
        """
        Equation: 17.8
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1e79011e8601?v=0.7.0
        """
        tranche_index =  (CURRENT_TIME() - (SLOT_PERIOD * int(header_slot))) // AUDIT_PERIOD
        return tranche_index


    @staticmethod
    def validator_announcement_statement(assign_report: List[Tuple[CoreIndex, WorkReport]], header: Header, ed25519_public: Ed25519Public, tranche: U8) -> Ed25519Signature:
        """
        Equation: 17.9, 17.10, 17.11
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1ea5011eea01?v=0.7.0
        """

        sign_announcement = None

        signing_context = Bytes(SIGNING_CONTEXTS["announce"])

        header_hash = Bytes(Hash.blake2b(header.encode()))

        report_encode = b""

        set_value : set = set()

        for c, r in assign_report:
            report_encode = Bytes(c.encode() + Hash.blake2b(r.encode()))
            set_value.add(report_encode)
            report_encode = b""

        set_encode = Bytes(b"")

        for item in set_value:
            set_encode = item.encode() + set_encode


        context = signing_context + Bytes(tranche) + set_encode + header_hash

        sign_announcement = signature_pvt(key=ed25519_public, context=context)

        return Ed25519Signature(sign_announcement)

    def refine(self, p: WorkPackage, c: CoreIndex, e:Extrinsics, r_hash: WorkReportHash, wr: WorkReport) -> bool:
        """
        Equation: 17.17
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1f2f011f6c01?v=0.7.0
        """
        from jam.work_package.processor import Processor


        # construct Work package Bundle using protocol => CE138
        # bundle = WorkPackageBundle()
        # lookup = Dictionary({})


        processor = Processor(node=self.node)
        w_r, wr_hash = processor.process(package=p, core=c, extrinsics=e)
        # print(w_r)
        # print("PROCESS HASH =>", type(wr_hash), wr_hash.hex())
        # print("GIVEN HASH=>", type(r_hash), r_hash.hex())
        # print("ER ROOT", w_r.package_spec.erasure_root.hex(), wr.package_spec.erasure_root.hex())
        # print("SEG ROOT", w_r.package_spec.exports_root.hex(), wr.package_spec.exports_root.hex())
        # print("Package hash", w_r.package_spec.hash.hex(), wr.package_spec.hash.hex())
        # print("RESULTS", w_r.results == wr.results)
        # print("OTH ", w_r.auth_output == wr.auth_output)

        # try:
        #     from deepdiff import DeepDiff
        #     value_diff = DeepDiff(wr.to_json(), w_r.to_json(), significant_digits=0, verbose_level=2)
        #     assert value_diff == {}, f"\nValue Diff: {value_diff.pretty()}"
        #     # for got, expected in zip(w_r, wr):
        #     assert w_r == wr
        # except AssertionError as e:
        #     print(f"ERROR ASSERTING: {e}")
        if wr_hash == r_hash:
            return True
        else:
            return False


    def judgment_signature(self, r: WorkReport, refine: bool, ed25519_public: Ed25519Signature) -> Bytes[96]:
        """
        Equations: 17.18
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1f6f011f9801?v=0.7.0
        """
        context = Bytes(b"")

        # print("YHA TAK BHI CHAL GYA ")

        if refine:
            context = SIGNING_CONTEXTS["valid"] + Hash.blake2b(r.encode())
        else:
            context = SIGNING_CONTEXTS["invalid"] + Hash.blake2b(r.encode())

        signature = signature_pvt(key=ed25519_public, context=Bytes(context))
        # print("22222222222222222222222222222222222222222222222222")
        # print("SSSSIGGNNAAATTTUUUURREEE", len(BandersnatchVrfSignature(signature).encode()), BandersnatchVrfSignature(signature).hex())

        return BandersnatchVrfSignature(signature)


    def audited_report(self, pre_audit: List[Option[WorkReport]]) -> TypedVector[Option[WorkReport]]:
        """
        Equation: 17.19, 17.20
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1fa9011fd301?v=0.7.0
        """


        # condition 1 => on that core all the judgment should be true and A_n(r) ⊂ J_T(r
        # condition 2 => if in tranche all the judgment of the validator should be > 2/3
