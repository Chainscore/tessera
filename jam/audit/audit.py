from docutils.nodes import header
from dataclasses import dataclass

from sympy.printing.aesaracode import mapping

from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.types import WorkExecResult, Null, ByteArray32
from jam.types.base.dictionary import V
from jam.types.work.report import WorkReport
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.state.components.sigma import Sigma
from jam.state.components.rho import Rho, OptionalWorkReportState, WorkReportState
from jam.utils.codec import Codable
from jam.utils.codec.decorators import decodable_dataclass
from jam.utils.constants import CORE_COUNT
from jam.ring_vrf.vrf import VRF
from jam.types.header import Header
from jam.utils.constants import SIGNING_CONTEXTS
from jam.utils.json import JsonSerde
from jam.utils.shuffle import fisher_yates_with_hash, shuffle

'''-------------------------Available work report------------------------------------'''
@decodable_dataclass
@dataclass
class WorkReportAvail(Codable, JsonSerde):
    workreport: WorkReport


@decodable_vector(max_length=CORE_COUNT)
class WorkReportsAvailable(Vector[WorkReportAvail]):
    """Vector of Work Reports"""

# TODO: PreAuditWorkreport is the list of Available work_report from the RHO_DOUBLE_DECKER (which comes from assurance section )
""" This is dummy for now """
@decodable_vector(max_length=CORE_COUNT, element_type=WorkReport)
class PreAuditWorkreport(Vector[WorkReport]):
    AuditReport : WorkReport

class AuditingAndJudgement:


    def __init__(self):
        self.vrf = VRF

    @staticmethod
    def report_to_be_audit( state : Sigma):
        core_report_mapping = []
        """
        This function returns sequence of work-reports which we may be required to audit.
        """
        for x in state.rho:
            if x is not Null:
                if x.report in WorkReportsAvailable:
                    core_report_mapping.append(x.report)
        return

    @staticmethod
    def verifiable_random_quality(entropy: Header):

        entropy_yield_vrf_signature = entropy.entropy_source

        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)

        bandersnatch_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(bytes(entropy_yield_vrf_signature)))[:32]

        random_quantity = bytes(SIGNING_CONTEXTS["audit"]) + bandersnatch_proof

        return random_quantity


    @staticmethod
    def non_empty_item(header: Header, vrf: VRF):

        """
        Equations:
            1. r = y(So)
            2. p = f([(c, Qc) | c <- Nc ], r )
            3. ao = {(c, w) | (c, w) E p... + 10, w != Phi }
        """

        # Equations : 17.7 (r = y(So))
        vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
        entropy = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(AuditingAndJudgement.verifiable_random_quality(entropy=header)))[:32]

        # Equation :  17.6 p = f([(c, Qc) | c <- Nc ], r )
        # core, report mapping


        mapping = {}
        mapping  = []
        for i in range(CORE_COUNT):
            key = i
            value = PreAuditWorkreport[i]
            if key not in mapping:
                mapping[key] = set()
            mapping[key].add(value)
        mapping = {k: mapping[k] for k in sorted(mapping.keys())}


        shuffling =  shuffle(h=, array=)















