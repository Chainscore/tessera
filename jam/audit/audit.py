from typing import List, Tuple

from tsrkit_types import structure, Null, TypedVector, Bytes, Uint, Option, U8, U32

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jam.types.protocol.core import CoreIndex, TimeSlot, TrancheIndex, ValidatorIndex

from jam.types.work.report import WorkReport
from jam.utils.constants import (
    CURRENT_TIME,
    SLOT_PERIOD,
    AUDIT_PERIOD,
    SIGNING_CONTEXTS,
    VALIDATOR_COUNT,
)
from jam.utils.shuffle import shuffle
from jam.types.protocol.crypto import Hash, BandersnatchPublic
from jam.types.protocol.core import TrancheIndex
from jam.types import BandersnatchVrfSignature, Ed25519Signature
from jam.types.work.package import WorkPackage

from jam.block.header import Header

# from jam.types.state.rho import OptionalWorkReportState, Rho
from jam.logging import get_logger
# from jam.audit.utils import sign_bandersnatch, audit_refine
from py_ark_vrf import prove_ietf, vrf_output


from jam.types.work.manifest import Extrinsics

from jam.audit.utils import audit_refine

# Module-specifier logger
logger = get_logger("in_core")


class AuditingAndJudgement:


    @staticmethod
    def report_to_be_audit(
        pending_wrs: List[Option[WorkReport]], newly_avail_wrs: List[Option[WorkReport]]
    ) -> List[Option[WorkReport]]:
        """
        Equation: 17.1, 17.2
        This functions as a mapping of core index to a work-report pending which has just become available, or ∅ if no report became available on the core.

        Args:
            newly_avail_wrs: Reports just become available after assurances
            pending_wrs: Pending Work Reports (Rho)

        Returns:
            A sequence of length equal to the number of cores

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1e61001eb600?v=0.7.0
        """

        pre_audit_report: List[Option[WorkReport]] = []

        # for i, report in enumerate(pending_wrs):
        #     if report is not Null:
        #         if report in newly_avail_wrs[i]:
        #             pre_audit_report.append(report["report"])
        #         else:
        #             pre_audit_report.append(Null)
        #     else:
        #         pre_audit_report.append(Null)

        for i in range(len(pending_wrs)):
            value1 = pending_wrs[i]
            value2 = newly_avail_wrs[i]

            if value1 is None:
                pre_audit_report.append(Null)
            else:
                if value1 == value2:
                    pre_audit_report.append(value1)
                else:
                    pre_audit_report.append(Null)

        return pre_audit_report

    @staticmethod
    def vrf_signature_bandersnatch(
        entropy_source: BandersnatchVrfSignature,
        bandersnatch_key: BandersnatchPublic,
        tranche_index: TrancheIndex = None,
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

        entropy_vrf_proof = BandersnatchVrfSignature(prove_ietf(entropy_source.encode(), input_data=b"", aux=b""))

        context = SIGNING_CONTEXTS["audit"] + entropy_vrf_proof

        if tranche_index != TrancheIndex(0):
            context += Bytes(Hash.blake2b(w_r.encode())) + tranche_index

        signature = prove_ietf(
                bandersnatch_key,
                context, b""
        )

        return BandersnatchVrfSignature(signature)

    @classmethod
    def verifiable_random_selection(
        cls,
        entropy_source: BandersnatchVrfSignature,
        bandersnatch_key: BandersnatchPublic,
        pre_audit_report: List[Option[WorkReport]],
        tranche_index: TrancheIndex
    ) -> List[Tuple[CoreIndex, WorkReport]]:
        """
        Equation: 17.5, 17.6
        Here in this function we just take q(report_to_be_audit function above) , shuffled it and get initial 10 Work Reports assign to validator.

        Args:
            entropy_source:
            bandersnatch_key:
            pre_audit_report:
            tranche_index:

        Return:
            Random initial 10 not Null Work Reports

        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1e0a011e5601?v=0.7.0
        """

        entropy = vrf_output(cls.vrf_signature_bandersnatch(entropy_source=entropy_source, bandersnatch_key=bandersnatch_key, tranche_index=tranche_index, w_r=None))
        print("ENTROPY ENTROPY ENTROPY ENTROPY ENTROPY ENTROPY", len(entropy))

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
    async def audit_refine(
        p: WorkPackage,
        c: CoreIndex,
        e: Extrinsics,
        wr: WorkReport,
        node_index: ValidatorIndex,
    ) -> bool:
        """
        Equation: 17.17
        Here we Build whole Work Package bundle and refine it, which gives Work Report amd Report Hash, later check with given work report and return bool value.

        Args:
            p:
            c:
            e:
            wr:
            node_index:

        Return:
            Boolean value , True or False

        Source: https://graypaper.fluffylabs.dev/#/38c4e62/1f2f011f6c01?v=0.7.0
        """

        from jam.network.node import node

        # TODO: construct Work package Bundle using protocol => CE138
        # TODO: Condition check after building package => 1. W_p hash with Wr->spec->hash, 2.import Segments, 3. Export segments, 4. Extrinsic
        # TODO: Final Report hashes values and return True and False

        from jam.network.protocols.ce_138 import CE138Data, AuditShardRequestProtocol
        from jam.network.protocols.ce_137 import Query
        from jam.types.protocol.core import ErasureRoot
        from jam.types.work.shard import ShardIndex
        from jam.utils.chainspec import chain_config
        from jam.incore.processor import Processor

        # CE138 = AuditShardRequestProtocol()
            # process = Processor(node=node)
        # erasure_root = ErasureRoot(wr.package_spec.erasure_root)
        #
        # # For this node shard index and validator index information is:
        # v_i = node_index
        # s_i = get_si(validator_index=v_i, core_index=wr.core_index)
        #
        # # For other node to get shard data, from which node that shard
        # total_shard = VALIDATOR_COUNT

        # for i in range(VALIDATOR_COUNT):
        #     if i != s_i:
        #         request_s_i = i
        #         request_v_i = get_vi(shard_index=request_s_i, core_index=wr.core_index)
        #         query = Query(erasure_root=erasure_root, shard_index=ShardIndex(2))
        #         data = CE138Data(len=U32(len(query.encode())), query=query)
        #
        #         data = await CE138.transmit(node=node, data=data, node_index=ValidatorIndex(1))

        w_r, wr_hash = audit_refine(package=p, core=c, extrinsics=e)

        r_hash = Hash.blake2b(wr.encode())

        if wr_hash == r_hash:
            return True
        else:
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
