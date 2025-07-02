from typing import List, Optional
from tsrkit_types import TypedVector
from jam.ring_vrf.curve.specs.bandersnatch import Bandersnatch_TE_Curve, BandersnatchPoint
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.types.work.package import WorkPackage
from jam.types.work.report import WorkReport

def power_set(input_list: TypedVector, length: Optional[int] = None) -> TypedVector[TypedVector]:
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


# def F(work_report: WorkReport) -> bytes:
#     """
#     F(w) function: will fetch wp encoding and
#     reconstructing the Erasure Coded Chunks (Through Erasure coding's Merkle root)
#     refer equ 17.17
#     """
#     # TODO: Do as per comment.
#     # NOTE: Currently its a dummy
#     return work_report.encode()


def bandersnatch_y(key: bytes):
    entropy_yield_vrf_signature = key
    vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
    bandersnatch_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(entropy_yield_vrf_signature))[:32]
    return bandersnatch_proof

def bandersnatch_f(key,context,message:bytes=b""):
    vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
    output_point, proof=  vrf.prove(alpha=message, secret_key=key,  additional_data=context, salt=b"")
    op_bt_str= output_point.point_to_string()

    proof_bt_str= proof[0].to_bytes()+ proof[1].to_bytes()
    signature= op_bt_str + proof_bt_str
    return signature

