from typing import List, Optional

from jam.ring_vrf.curve.specs.bandersnatch import Bandersnatch_TE_Curve, BandersnatchPoint
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.types.base.integers.general import Int
from jam.types.base.sequences.bytes.byte_array import ByteArray64, ByteArray96
from jam.types.work.package import WorkPackage
from jam.types.work.report import WorkReport

def power_set(input_list: List, length: Optional[int] = None) -> List[List]:
    """
    Compute the power set of the given list. Optionally, limit to subsets of a specific length.

    Args:
    - input_list: A list of elements.
    - length: An optional parameter to limit the power set to subsets of this length.

    Returns:
    - A list of lists, where each sublist is a subset of the input_list.
      If length is specified, only subsets of that length are included.
    """
    power_set_result = [[]]  # Start with the empty set

    for item in input_list:
        # For each item in the input_list, create new subsets by adding the item to existing subsets
        new_subsets = [subset + [item] for subset in power_set_result]
        power_set_result.extend(new_subsets)  # Add the new subsets to the power_set_result

    # If length is provided, filter subsets to match the specified length
    if length is not None:
        power_set_result = [subset for subset in power_set_result if len(subset) == length]

    return power_set_result


def F(work_report: WorkReport) -> bytes:
    """
    F(w) function: will fetch wp encoding and
    reconstructing the Erasure Coded Chunks (Through Erasure coding's Merkle root)
    refer equ 17.17
    """
    # TODO: Do as per comment.
    # NOTE: Currently its a dummy
    return work_report.encode()

def Ξ(work_package: WorkPackage,core_index:Int)->WorkReport:
    """
    Ξ as mentioned in equ 17.17 take package and core index and give out a workreport
    if the condition is True then only
    As per Eqn 14.11 its already build but not getting expected result so for the timing

    NOTE: This Dummy Func got introduced
    TODO: Need to remove after the main func is implemented
    """

    return WorkReport.empty()


# def Bandersnatch_F(key):

def Bandersnatch_y(key:ByteArray96):
    entropy_yield_vrf_signature = key
    vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
    bandersnatch_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(bytes(entropy_yield_vrf_signature)))[:32]
    return bandersnatch_proof
