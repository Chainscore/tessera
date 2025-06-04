from dataclasses import dataclass
from typing import List, Set, Tuple

from jam.types.base.sequences.bytes.byte_array import ByteArray64
from jam.types.protocol.core import CoreIndex
from rich.diagnose import report
from sympy import floor
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.types import WorkExecResult, Null, ByteArray32, TimeSlot, Int
from jam.types.work.report import WorkReport
from jam.state.components.sigma import Sigma
from jam.utils.constants import CORE_COUNT, CURRENT_TIME, SLOT_PERIOD, AUDIT_PERIOD
from jam.ring_vrf.vrf import VRF
from jam.types.header import Header
from jam.utils.constants import SIGNING_CONTEXTS
from jam.utils.shuffle import shuffle
from jam.types.protocol.crypto import Hash
from jam.assurances.assurances import Assurances
from jam.types.block import Block


@dataclass
class AuditingAndJudgement:

    def __init__(self):
        self.vrf = VRF
        self.assurance = Assurances.transition(state=Sigma, block=Block)


    def report_to_be_audit(self, state: Sigma)->List[WorkReport]:
        """
        Function Q define in Eq. 17.1 and 17.2
        This function define the sequence of work_report which required to audit(Q)

        Source:
            https://graypaper.fluffylabs.dev/#/9a08063/1e31001e7400?v=0.6.6

        Args:
            state : Pending Work Reports

        Returns:
            Array of Work Reports to be Audit
        """

        pre_auditing_report = []

        for i, (report, slot) in enumerate(state.rho):
            if report in self.assurance:
                pre_auditing_report.append(report)
            else:
                pre_auditing_report.append(Null)

        return pre_auditing_report

    @staticmethod
    def verifiable_random_quality(header: Header):
        """
        Function So define in Eq. 17.3 and 17.4

        Sources:
            https://graypaper.fluffylabs.dev/#/9a08063/1e89001e9c00?v=0.6.6

        Args:
            header : Header for fetchign its entropy (H_v)

        Returns:
             randomness for entropy
        """

        entropy_yield_vrf_signature = header.entropy_source

        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)

        bandersnatch_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(bytes(entropy_yield_vrf_signature)))[:32]

        random_quantity = bytes(SIGNING_CONTEXTS["audit"]) + bandersnatch_proof

        return random_quantity

    # Verifiable Random Selection Function (within 10 cores) a_n
    def vrs_func(self, header: Header, state: Sigma) -> List[Tuple[CoreIndex, WorkReport]]:

        """
        This function give the non-empty-item to audit through a verifiable random selection of ten cores:

        Sources:
            https://graypaper.fluffylabs.dev/#/9a08063/1ebc001e1701?v=0.6.6

        Equations:
            17.7 r = y(So)
            17.6 p = f([(c, Qc) | c <- Nc ], r )
            17.5 ao = {(c, w) | (c, w) E p... + 10, w != Phi }
        """

        # Equation : 17.7 (r = y(So))
        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
        entropy = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(AuditingAndJudgement.verifiable_random_quality(header=header)))[:32]

        # Equation :  17.6 p = f([(c, Qc) | c <- Nc ], r )
        audit_report = self.report_to_be_audit(state)
        core_report =  [(c, w_r) for c, w_r in enumerate(audit_report)]

        shuffle_report = shuffle(entropy, core_report)

        # Eq. 17.5 : ao = {(c, w) | (c, w) E p... + 10, w != Phi }
        vrs_list = [(c, w) for (c, w) in shuffle_report if w is not Null]

        return vrs_list

    # Generate Tranche Index
    @staticmethod
    def generate_tranche_index( header : Header, state: Sigma) -> int:
        """
        Eq. 17.8

        This function gives the current tranche (how many tranches have passed since the report became available).

        Sources:
            https://graypaper.fluffylabs.dev/#/9a08063/1e21011e3501?v=0.6.6

        """
        tranche_index =  (CURRENT_TIME() - (SLOT_PERIOD * int(header.slot))) // AUDIT_PERIOD
        return tranche_index

    def validator_statement(self, header: Header, state: Sigma)->List[ByteArray64]:
        """
        Eq. 17.9, 17.10, 17.11

        """
        #17.11
        singing_context = bytes(SIGNING_CONTEXTS["jam_announce"])
        #17.10
        tranches_index = self.generate_tranche_index(header, state) #n
        vrs_list=self.vrs_func(header,state)
        vrs_bytes=bytes()
        #Serializing the vrs_list -> x_n
        for (core,wr) in vrs_list:
            vrs_bytes+=core.encode()+ Hash.blake2b(wr.encode()).encode()

        #17.9
        #loop through the validators and signing the message with their ed25519publickey
        announcement_statement = singing_context + bytes(tranches_index) + vrs_bytes + bytes(Hash.blake2b(header.encode())) #S
        statement_set=[]
        for validator in state.kappa:
            private_key = Ed25519PrivateKey.from_private_bytes(bytes(validator.ed25519))
            # Sign will give out a 64Byte Signature
            signature = private_key.sign(announcement_statement)
            # Explicitely modifying to the ByteArray64 format
            statement_set.append(ByteArray64(signature))

        return statement_set
