from dataclasses import dataclass
from typing import List, Tuple

from tsrkit_types import Null, TypedVector, Bytes, Uint, Option, U8, Bool, Dictionary

from jam.audit.vectors.reports import reports
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
from jam.work_package.processor import Processor

from jam.types.block.header import Header
from jam.types.state.rho import Rho

from jam.audit.utils import signature_pvt

from jam.network.node import Node
from jam.state.state import State




@dataclass
class AuditingAndJudgement:

    node: Node

    def __init__(self, node: Node):
        from jam.settings import settings
        self.settings = settings
        self.vrf = VRF
        self.node = node
        self.state = State

    @staticmethod
    def report_to_be_audit(available_reports: Rho, pending_report: Rho) -> List[Option[WorkReport]]:
        """
        Function Q define in Eq. 17.1 and 17.2
        This function define the sequence of work_report which required to audit(Q)

        Source:
            https://graypaper.fluffylabs.dev/#/9a08063/1e31001e7400?v=0.6.6

        Args:
            available_reports : Pending Work Reports
            pending_report: report, rho contains

        Returns:
            Array of Work Reports to be Audit
        """

        pre_audit_report = List[Option[WorkReport]]([])

        for i, (report, slot) in enumerate(pending_report):
            if report in available_reports:
                pre_audit_report.append(report)
            else:
                pre_audit_report.append(Null)

        return pre_audit_report

    @staticmethod
    def vrf_signature_bandersnatch(entropy_source: BandersnatchVrfSignature, bandersnatch_key: BandersnatchPublic, tranche_index: U8 = None, w_r: WorkReport = None ) -> Bytes[96]:
        """
        Equation: 17.3, 17.4
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1ec1001e0001?v=0.7.0
        """
        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)

        entropy_vrf_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(entropy_source.encode()))[:32]
        random_quantity = Bytes(SIGNING_CONTEXTS["audit"]) + entropy_vrf_proof

        if tranche_index is not Null and tranche_index > 0 and w_r is not Null:
            random_quantity += Bytes(Hash.blake2b(w_r.encode())) + Bytes(tranche_index)

        signature = signature_pvt(key=bandersnatch_key, context=random_quantity)

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

        # ------------------------------------- audit size array and shuffle --------------------------------------------
        array_index = TypedVector[Uint[32]]([])
        for i in range(len(pre_audit_reports)):
            array_index.append(Uint[32](i))

        shuffle_array = shuffle(entropy, array_index)

        # ------------------------------------------ updated shuffle auditing list -------------------------------------
        lookup = dict(core_indexes)
        updated_array : List[tuple[core_indexes, Option[WorkReport]]] = [(CoreIndex(i), lookup[i]) for i in shuffle_array]

        # ------------------------------------------ take initial 10 values --------------------------------------------
        # Eq. 17.5 : ao = {(c, w) | (c, w) E p... + 10, w != Phi }
        shuffle_not_null  = [(c, w) for (c, w) in updated_array if w is not Null][:10]

        return shuffle_not_null

    @staticmethod
    def generate_tranche_index(header_slot: TimeSlot) -> U8:
        """
        Equation: 17.8
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1e79011e8601?v=0.7.0
        """
        tranche_index =  (CURRENT_TIME() - (SLOT_PERIOD * int(header_slot))) // AUDIT_PERIOD
        return tranche_index


    @staticmethod
    def validator_announcement_statement(assign_report: List[Tuple[CoreIndex, WorkReport]], header: Header, ed25519_public: Ed25519Public, tranche: U8) -> set[Bytes[64]]:
        """
        Equation: 17.9, 17.10, 17.11
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1ea5011eea01?v=0.7.0
        """
        validator_announcement_set: set[Bytes[64]] = set()

        signing_context = Bytes(SIGNING_CONTEXTS["announce"])

        header_hash = Bytes(Hash.blake2b(header.encode()))

        context = signing_context + Bytes(tranche) + header_hash

        for c, r in assign_report:
            context = context + Bytes(c.encode() + Hash.blake2b(r.encode())).encode()
            signature = signature_pvt(key=ed25519_public, context=context)
            validator_announcement_set.add(signature)
            context = signing_context + Bytes(tranche) + header_hash

        return validator_announcement_set

    def refine(self, r: WorkReport) -> bool:
        """
        Equation: 17.17
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1f2f011f6c01?v=0.7.0
        """
        from jam.work_package.processor import Processor

        # construct Work package Bundle using protocol => CE138
        bundle = WorkPackageBundle()
        lookup = Dictionary({})

        core_index = r.core_index

        processor = Processor(self.node)
        w_r, wr_hash = processor.process_bundle(core=core_index, bundle=bundle, sr_lookup=lookup)

        if wr_hash == r:
            return True
        else:
            return False


    def judgment_signature(self, r: WorkReport, refine: bool, ed25519_public: Ed25519Signature) -> Bytes[96]:
        """
        Equations: 17.18
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1f6f011f9801?v=0.7.0
        """
        context = Bytes()

        if refine:
            context = SIGNING_CONTEXTS["valid"] + Hash.blake2b(r.encode())
        else:
            context = SIGNING_CONTEXTS["invalid"] + Hash.blake2b(r.encode())

        signature = signature_pvt(key=ed25519_public, context=context)
        return signature


    def audited_report(self, pre_audit: List[Option[WorkReport]]) -> TypedVector[Option[WorkReport]]:
        """
        Equation: 17.19, 17.20
        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1fa9011fd301?v=0.7.0
        """


        # condition 1 => on that core all the judgment should be true and A_n(r) ⊂ J_T(r
        # condition 2 => if in tranche all the judgment of the validator should be > 2/3


