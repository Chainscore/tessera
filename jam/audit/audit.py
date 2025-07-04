from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from tsrkit_types import Null, Bytes, TypedVector, U32, Bytes, Uint, Option
from jam.audit.utils import bandersnatch_f
from jam.network.protocols.ce_136 import OptRep
from jam.types.protocol.core import CoreIndex, TimeSlot, ValidatorIndex
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jam.types.work.report import WorkReport
from jam.state.state import State, state
from jam.types.block.header import Header
from jam.utils.constants import CORE_COUNT, CURRENT_TIME, SLOT_PERIOD, AUDIT_PERIOD, SIGNING_CONTEXTS
from jam.ring_vrf.vrf import VRF
from jam.utils.shuffle import shuffle
from jam.types.protocol.crypto import Hash, BandersnatchPublic
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.types import BandersnatchVrfSignature
from jam.types.work.report import WorkReportHash
from jam.types.protocol.merkle import OptionHash
from jam.types.work.package import WorkPackage
# from jam.work_package.processor import Processor
from tsrkit_types.sequences import TypedVector
from tsrkit_types.integers import Uint



@dataclass
class AuditingAndJudgement:
    state: State
    assurance: TypedVector[OptRep]
    tranche_index: int
    block: Header
    # In-memory ephemeral storage during the auditing process
    an_map: Dict[WorkReportHash, Set[ValidatorIndex]] = field(default_factory=dict)
    jt_map: Dict[WorkReportHash, Set[ValidatorIndex]] = field(default_factory=dict)
    jf_map: Dict[WorkReportHash, Set[ValidatorIndex]] = field(default_factory=dict)
    audited_wrs: Set[WorkReportHash] = field(default_factory=set)
    # def __init__(self, current_state, current_assurances):
    #     self.state = current_state
    #     self.assurance = current_assurances
    #     # self.process = Processor

    def report_to_be_audit(self,available_reports : TypedVector[OptRep]) -> TypedVector[OptRep]:
        """
        Function Q define in Eq. 17.1 and 17.2
        This function define the sequence of work_report which required to audit(Q)

        Source:
            https://graypaper.fluffylabs.dev/#/9a08063/1e31001e7400?v=0.6.6

        Args:
            available_reports : Pending Work Reports

        Returns:
            Array of Work Reports to be Audit
        """

        pre_auditing_report =  TypedVector[OptRep]([])
        for i, (report, slot) in enumerate(self.state.rho):
            if report in available_reports:
                pre_auditing_report.append(report)
            else:
                pre_auditing_report.append(Null)

        return pre_auditing_report

    @staticmethod
    def vrf_signature_bandersnatch(entropy_source: BandersnatchVrfSignature, bandersnatch_key: BandersnatchPublic, tranche_index: int = 0, work_report: Optional[WorkReport] = None) -> Bytes[96]:
        """
        s_0: The initial VRF (Verifiable Random Function) signature used to select work-reports for auditing in the first tranche (n=0).

        Sources:
            https://graypaper.fluffylabs.dev/#/9a08063/1e89001e9c00?v=0.6.6

        Args:
            entropy_source: Entropy_Source from Block's header
            bandersnatch_key:
            tranche_index:
            w_report: Work Report

        Returns:
             randomness for entropy

        refer 17.3 && 17.15
        """

        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)

        entropy_vrf_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(entropy_source.encode()))[:32]

        random_quantity = Bytes(SIGNING_CONTEXTS["audit"]) + entropy_vrf_proof  # Xv + y(Hv)

        key = int.from_bytes(Bytes.fromhex(str(bandersnatch_key)))

        output_point, proof = vrf.prove(alpha=b"", secret_key=key, additional_data=random_quantity, salt=b"")
        op_bt_str = output_point.point_to_string()

        proof_bt_str = proof[0].to_bytes(32, 'little') + proof[1].to_bytes(32, 'little')
        signature = op_bt_str + proof_bt_str  # Expected S0 (96bytes)

        if tranche_index is not Null and tranche_index > 0 and work_report is not None:
            random_quantity += Bytes(Hash.blake2b(work_report.encode()).encode()) + Bytes(tranche_index)  # refer 17.15

        return signature


    def vrs_func(self, entropy_source: BandersnatchVrfSignature, bandersnatch_key: BandersnatchPublic,tranch_index:int,work_report:Optional[WorkReport]=None) -> List[Tuple[CoreIndex, WorkReportHash]]:
        """
        This is basically a_n assigns certain wr_list to the validator whose bandersnatck key we are passing as args
        s_n(Hv,validator_bandersnatch,tranche_index,work_report)

        refer 17.16
        """
        # Equation : 17.7 (r = y(So))
        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
        entropy = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(self.vrf_signature_bandersnatch(entropy_source=entropy_source, bandersnatch_key=bandersnatch_key,tranche_index=tranch_index,work_report=work_report)))[:32]

        #  Equation :  17.6 p = f([(c, Qc) | c <- Nc ], r )
        audit_report = self.report_to_be_audit(self.assurance)
        core_indexes = TypedVector[Tuple[Uint[32], WorkReportHash]]([])
        for c, w_r in enumerate(audit_report):
            core_indexes.append((Uint[32](c), Optional[WorkReportHash(w_r)]))

        #------------------------------------- audit size array and shuffle --------------------------------------------
        array_index = TypedVector[Uint[32]]([])
        for i in range(len(audit_report)):
            array_index.append(Uint[32](i))

        shuffle_array = shuffle(entropy, array_index)
        print("shuffle randon array => ", shuffle_array)

        # ------------------------------------------ updated shuffle auditing list -------------------------------------
        lookup = dict(core_indexes)
        updated_array = [(i, lookup[i]) for i in shuffle_array]
        print(updated_array)

        # ------------------------------------------ take initial 10 values -------------------------------------
        # Eq. 17.5 : ao = {(c, w) | (c, w) E p... + 10, w != Phi }

        shuffle_not_null = [(c, w) for (c, w) in updated_array if w is not Null][:10]

        return shuffle_not_null


    @staticmethod
    def generate_tranche_index(header_slot: TimeSlot) -> Uint:
        """
        Eq. 17.8

        This function gives the current tranche (how many tranches have passed since the report became available).

        Sources:
            https://graypaper.fluffylabs.dev/#/9a08063/1e21011e3501?v=0.6.self6

        """
        tranche_index =  (CURRENT_TIME() - (SLOT_PERIOD * int(header_slot))) // AUDIT_PERIOD
        return tranche_index


    def validator_announcement_statement(self, header: Header, validator_index: ValidatorIndex) -> bytes:
        """
        Validator’s announcement statements must be in the set S
        refer to Eq. 17.9
        """

        # Ed25519 Audit announcement statements
        signing_context = bytes(SIGNING_CONTEXTS["jam_announce"])

        # n (tranche index)
        tranches_index = self.generate_tranche_index(header.slot)

        # block's header hash
        header_hash = bytes(Hash.blake2b(header.encode()))

        # x_n  => Serializing the vrs_list -> x_n
        vrs_list=self.vrs_func(header.entropy_source,self.state.kappa[validator_index].bandersnatch,tranches_index)
        vrs_bytes=bytes()
        for (core,wr) in vrs_list:
            vrs_bytes += core.encode() + Hash.blake2b(wr.encode()).encode()

        #loop through the validators and signing the message with their ed25519publickey
        announcement_context= signing_context + bytes(tranches_index) + vrs_bytes +  header_hash

        statement_signature : bytes= bandersnatch_f(key=self.state.kappa[validator_index].ed25519,context=announcement_context)


        return statement_signature
    #
    # def evaluate_core_mappings (self, core_index: int , package: WorkPackage, ):
    #     # refer 17.17
    #     if F(w)  ==  self.rho[w_r.core_index].encode():
    #         return self.process.process_bundle(core=core_index, bundle=package, sr_lookup=)
    #     else:
    #         return False


    def validator_judment_mapping(self,header:Header,validator_index:ValidatorIndex,isTrue:Optional[bool]=None,tranche_index:int=0)-> list[bytes] :
        """
         Go through the evaluate_core_mappings Func (refer 17.17) and provide its validity where the wr is valid or not
         Return :
            Set of Judgment signatures from each (kappa/current) validator
        refer equ 17.18
        """
        # judgement_map={True:[],False:[]} # later on might change to list of judgement (Judgement Signatures)
        judgment_list=[]
        private_key = Ed25519PrivateKey.from_private_bytes(bytes(self.state.kappa[validator_index].ed25519))
        a_n=self.vrs_func(header.entropy_source,self.state.kappa[validator_index].bandersnatch,tranche_index)
        for core_index,wr_hash in enumerate(a_n):

            # signing_context = SIGNING_CONTEXTS["valid"] if evaluate_core_mappings(wr_hash) else SIGNING_CONTEXTS["invalid"]
            signing_context = SIGNING_CONTEXTS["valid"] if True else SIGNING_CONTEXTS["invalid"]

            message= signing_context + )
        signature = private_key.sign(message)
                # Explicitely modifying to the ByteArddddray64 format
        judgment_list.append(bytes(signature))
        return judgment_list
