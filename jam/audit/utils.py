from typing import List, Optional

from docutils.frontend import validate_url_trailing_slash
from tsrkit_types import TypedVector
from tsrkit_types.bytes import Bytes
from jam.ring_vrf.curve.specs.bandersnatch import Bandersnatch_TE_Curve, BandersnatchPoint
from jam.ring_vrf.curve.specs.ed25519 import Ed25519_TE_Curve, Ed25519Point
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.types.work.report import WorkReport
from jam.types.protocol.core import ValidatorIndex

public_key = Bytes[32]

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


def signature_pvt(key: Bytes[32], context: Bytes, message:bytes=b"") :

    key = int.from_bytes(key)
    vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
    # Vrf2 = IETF_VRF(Ed25519_TE_Curve, Ed25519Point)
    output_point, eproof = vrf.prove(alpha=message, secret_key=key,  additional_data=context, salt=b"")
    op_bt_str= output_point.point_to_string()
    proof_bt_str= proof[0].to_bytes(32, 'little')+ proof[1].to_bytes(32, 'little')
    signature= op_bt_str + proof_bt_str

    return signature


