from dataclasses import dataclass
from typing import Set

from rich.diagnose import report
from sympy import floor
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.types import WorkExecResult, Null, ByteArray32, TimeSlot, Int
from jam.types.work.report import WorkReport
from jam.state.components.sigma import Sigma
from jam.utils.constants import CORE_COUNT, SLOT_PERIOD, AUDIT_PERIOD
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


    def report_to_be_audit(self, state: Sigma):
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
    def verifiable_random_quality(entropy: Header):
        """
        Function So define in Eq. 17.3 and 17.4

        Sources:
            https://graypaper.fluffylabs.dev/#/9a08063/1e89001e9c00?v=0.6.6

        Args:
            entropy : Entropy-yielding VRF signature (Hv Block's Header components)

        Returns:
             randomness for entropy
        """

        entropy_yield_vrf_signature = entropy.entropy_source

        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)

        bandersnatch_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(bytes(entropy_yield_vrf_signature)))[:32]

        random_quantity = bytes(SIGNING_CONTEXTS["audit"]) + bandersnatch_proof

        return random_quantity


    def non_empty_item(self, header: Header, state: Sigma):

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
        entropy = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(AuditingAndJudgement.verifiable_random_quality(entropy=header)))[:32]

        # Equation :  17.6 p = f([(c, Qc) | c <- Nc ], r )
        audit_report = self.report_to_be_audit(state)
        core_report =  [(c, w_r) for c, w_r in enumerate(audit_report)]

        shuffle_report = shuffle(entropy, core_report)

        # Eq. 17.5 : ao = {(c, w) | (c, w) E p... + 10, w != Phi }
        variable_random_selection = set()
        for item in shuffle_report:
            if item is not Null:
                variable_random_selection.add(item)

        return variable_random_selection

    @staticmethod
    def current_tranches( header : Header, state: Sigma) -> floor:
        """
        Eq. 17.8

        This function gives the current tranche (how many tranches have passed since the report became available).

        Sources:
            https://graypaper.fluffylabs.dev/#/9a08063/1e21011e3501?v=0.6.6

        """
        tranches =  floor((state.tau - (SLOT_PERIOD * header.slot)) / AUDIT_PERIOD )
        return tranches

    def validator_statement(self, header: Header, report: WorkReport, state: Sigma):
        """
        Eq. !&.9, 17.10, 17.11

        """
        singing_context = bytes(SIGNING_CONTEXTS["jam_announce"])
        tranches_value = self.current_tranches(header, state)

        encode_core_work = (bytes(report.core_index.encode()) + bytes(Hash.blake2b(report.encode())))
        statements = singing_context + self.current_tranches(header, state) + encode_core_work + bytes(Hash.blake2b(header.encode()))