from dataclasses import dataclass
from typing import List, Optional, Set, Tuple
from tsrkit_types import Null, Bytes, Bytes64
from jam.types.protocol.core import CoreIndex, ValidatorIndex
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jam.types.work.report import WorkReport
from jam.state.state import state
from jam.utils.constants import CORE_COUNT, CURRENT_TIME, SLOT_PERIOD, AUDIT_PERIOD
from jam.ring_vrf.vrf import VRF
from jam.types.block.header import Header
from jam.utils.constants import SIGNING_CONTEXTS
from jam.utils.shuffle import shuffle
from jam.types.protocol.crypto import Hash, BandersnatchPublic
from jam.assurances.assurances import Assurances
from jam.types.block import Block
from jam.audit.utils import Ξ,F,power_set
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.types.work.package import WorkPackage
from jam.work_package.processor import Processor
from tsrkit_types.sequences import TypedVector
from tsrkit_types.integers import Uint



@dataclass
class AuditingAndJudgement:

    def __init__(self):
        self.vrf = VRF
        self.state,self.assurance = Assurances.transition(state=state, block=Block)
        self.process = Processor

    def report_to_be_audit(self) -> List[Optional[WorkReport]]:
        """
        Function Q define in Eq. 17.1 and 17.2
        This function define the sequence of work_report which required to audit(Q)

        Source:
            https://graypaper.fluffylabs.dev/#/9a08063/1e31001e7400?v=0.6.6

        Args:
            state : Pending Work Reports

        Returns:
            List of Optional[WorkReport] .
        """

        pre_auditing_report: List[Optional[WorkReport]] = []

        for i, (report, _slot) in enumerate(self.state.rho):
            if report in self.assurance:
                pre_auditing_report.append(report)
            else:
                pre_auditing_report.append(None)

        return pre_auditing_report

    def vrf_signature_bandersnatch(self, header: Header, validator_index: ValidatorIndex, tranche_index: int = 0, w_report: Optional[WorkReport] = None) -> Bytes[96]:
        """
        refer 17.3
        https://graypaper.fluffylabs.dev/#/cc517d7/1e89001e8f00?v=0.6.5

        s_0: The initial VRF (Verifiable Random Function) signature used to select work-reports for auditing in the first tranche (n=0).

        Sources:
            https://graypaper.fluffylabs.dev/#/9a08063/1e89001e9c00?v=0.6.6

        Args:
            header : Header for fetching its entropy (H_v)
            validator_index :
            tranche_index :
            w_report : Work Report

        Returns:
             randomness for entropy

        """

        entropy_yield = header.entropy_source

        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)

        entropy_vrf_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(bytes(entropy_yield)))[:32]

        random_quantity = bytes(SIGNING_CONTEXTS["audit"]) + entropy_vrf_proof #Xv + y(Hv)

        key = int.from_bytes(bytes.fromhex(str(self.state.kappa[validator_index]["bandersnatch"])))

        output_point, proof=  vrf.prove(alpha=b"" , secret_key=key,  additional_data=random_quantity,salt=b"")
        op_bt_str= output_point.point_to_string()

        proof_bt_str= proof[0].to_bytes()+ proof[1].to_bytes()
        signature= op_bt_str + proof_bt_str #Expected S0 (96bytes)

        if tranche_index > 0 and w_report is not None:
            random_quantity+= bytes(Hash.blake2b(w_report.encode()).encode()) + bytes(tranche_index) # refer 17.15

        # F Function needs to be implemented Here expected to return [sets of signatures]

        return signature

    # Verifiable Random Selection Function (within 10 cores) a_n
    def vrs_func(self, header: Header, validator_index:ValidatorIndex) -> List[Tuple[CoreIndex, WorkReport]]:

        """
        This function give the non-empty-item to audit through a verifiable random selection of ten cores:

        Sources:
            https://graypaper.fluffylabs.dev/#/9a08063/1ebc001e1701?v=0.6.6

        Equations:
            17.7 r = y(So)
            17.6 p = f([(c, Qc) | c <- Nc ], r )
            17.5 ao = {(c, w) | (c, w) E p... + 10, w != None }
        """

        # Equation : 17.7 (r = y(So))
        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
        entropy = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(self.vrf_signature_bandersnatch(header=header, validator_index=validator_index)))[:32]

         # Equation 17.6: p = f([(c, Qc) | c <- Nc ], r)
        audit_report = self.report_to_be_audit()
        core_indexes=TypedVector[Uint[32]]([])
        # indexes of c existing in the audit_report for shuffling on it
        for i, w_r in enumerate(audit_report):
            core_indexes.append(Uint[32](i))
        # Shuffle based on entropy
        shuffle_report = shuffle(entropy, core_indexes)

        # Eq. 17.5 : ao = {(c, w) | (c, w) E p... + 10, w != Null }tes64(signature))
        vrs_list:List[Tuple[CoreIndex, WorkReport]] = []
        for i in shuffle_report:
            if audit_report[i] is not None:
                vrs_list.append((CoreIndex(i), audit_report[i]))
            if len(vrs_list) == 10:
                break
        return vrs_list

    @staticmethod
    def generate_tranche_index(header : Header) -> int:
        """
        Eq. 17.8

        This function gives the current tranche (how many tranches have passed since the report became available).

        Sources:
            https://graypaper.fluffylabs.dev/#/9a08063/1e21011e3501?v=0.6.6

        """
        tranche_index =  (CURRENT_TIME() - (SLOT_PERIOD * int(header.slot))) // AUDIT_PERIOD
        return tranche_index

    def validator_announcement_statement(self, header: Header, state: state) -> set[Bytes64]:
        """
        Eq. 17.9, 17.10, 17.11
        This function define the sequence of work_report which required to audit(Q)

        Source:
            https://graypaper.fluffylabs.dev/#/7e6ff6a/1e6e011eba01?v=0.6.7

        Args:
            header (block's header H)
            state : get kappa from state for validator


        Returns:
            set of validator assi

        """

        # Ed25519 Audit announcement statements
        signing_context = bytes(SIGNING_CONTEXTS["jam_announce"])

        # n (tranche index)
        tranches_index = self.generate_tranche_index(header)

        # block's header hash
        header_hash = bytes(Hash.blake2b(header.encode()))

        # x_n  => Serializing the vrs_list -> x_n
        vrs_list=self.vrs_func(header,state)
        vrs_bytes=bytes()
        for (core,wr) in vrs_list:
            vrs_bytes += core.encode() + Hash.blake2b(wr.encode()).encode()

        #loop through the validators and signing the message with their ed25519publickey
        # S
        announcement_statement = signing_context + bytes(tranches_index) + vrs_bytes +  header_hash

        statement_set : set[Bytes[64]] = set()

        for validator in state.kappa:
            private_key = Ed25519PrivateKey.from_private_bytes(bytes(validator.ed25519))
            # Sign will give out a 64Byte Signature
            signature = private_key.sign(announcement_statement)
            # Explicitly modifying to the ByteArray64 format
            statement_set.add(signature)

        return statement_set

    # def evaluate_core_mappings (self, core_index: int , package: WorkPackage, ):
    #     # refer 17.17
    #     if F(w)  ==  self.rho[w_r.core_index].encode():
    #         return self.process.process_bundle(core=core_index, bundle=package, sr_lookup=)
    #     else:
    #         return False

    def validator_judment_mapping(self,work_report:WorkReport,state:state)-> List[Bytes[64]]:
        """
         Go through the evaluate_core_mappings Func (refer 17.17) and provide its validity where the wr is valid or not
         Return :
            Set of Judgment signatures from each (kappa/current) validator
        refer equ 17.18
        """
        judgement_set=[]
        for validator in state.kappa:
            private_key = Ed25519PrivateKey.from_private_bytes(bytes(validator.ed25519))
            signing_context = SIGNING_CONTEXTS["valid"] if evaluate_core_mappings(work_report) else SIGNING_CONTEXTS["invalid"]
            message= signing_context + Hash.blake2b(work_report.encode())
            # Sign will give out a 64Byte Signature
            signature = private_key.sign(message)
            # Explicitely modifying to the ByteArray64 format
            judgement_set.append(Bytes64(signature))
        return judgement_set
