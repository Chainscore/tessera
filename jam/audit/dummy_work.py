
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.ring_vrf.vrf import VRF
from jam.types.header import Header
from jam.utils.constants import SIGNING_CONTEXTS

# print("hii")
#
#
# class AAAMeta(type):
#     """Metaclass for defining Abstract Base Classes (ABCs)."""
#
# class AAA(metaclass=AAAMeta):
#     """Helper class that provides a standard way to create an ABC using
#     inheritance.
#     """
#     __slots__ = ()
#
# class Student(AAA):
#
#
#     def sum(self, a: int, b: int) -> int:
#         x = a*a
#         y = b*b
#         return x+y
#
#     def multi_sum(self, a: int, b :int ) -> int:
#         sum = Student.sum(a, b)
#         multiplie = sum*sum
#         return multiplie
"""-----------------------------------------------------------------------------"""


# from typing import List, Dict
#
# def create_number_alphabet_mapping() -> List[Dict[int, str]]:
#     mapping: List[Dict[int, str]] = [{i: chr(ord('a') + i)} for i in range(26)]
#     return mapping
#
# # Example usage
# mapping = create_number_alphabet_mapping()
# print(mapping[0][0])


# def report_to_be_audit():
#     core_report_mapping = []
#     """
#     This function returns sequence of work-reports which we may be required to audit.
#     """
#     for x in rho:
#         if x is not Null:
#             if x.report in WorkReportsAvailable:
#                 core_report_mapping.append(x.report)
#     return


def result():
    vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
    signature  = vrf.ecvrf_proof_to_hash(b'`\xf3/Z\xd3\xe9iK\x82\xcc\xc0\xa75\xed\xb2\xf9@\xf7W\xab3<\xc5\xf7\xb0\xa4\x11X\xb8\x0fWO\x8a\xa1\xc7U\xa0\nj%\xbd\xec\xda\x19~\xe1\xb6\n\x01\xe5\x07\x87\xbd\x10\xaa\x97a3\xf4\xc3\x91y3\x0e\x18\xc7O\xfdg\xe6\xab\xc6X\xe2\xd0^\xcd1\x01\xdd\xc0\xc36#\x82?#\x95S\x8c\xf8\xd3\x9eeO\x12')[:32]
    return signature

print("result here of signature => ", result())

def verifiable_random_quality():
    vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
    signature  = vrf.ecvrf_proof_to_hash(b'`\xf3/Z\xd3\xe9iK\x82\xcc\xc0\xa75\xed\xb2\xf9@\xf7W\xab3<\xc5\xf7\xb0\xa4\x11X\xb8\x0fWO\x8a\xa1\xc7U\xa0\nj%\xbd\xec\xda\x19~\xe1\xb6\n\x01\xe5\x07\x87\xbd\x10\xaa\x97a3\xf4\xc3\x91y3\x0e\x18\xc7O\xfdg\xe6\xab\xc6X\xe2\xd0^\xcd1\x01\xdd\xc0\xc36#\x82?#\x95S\x8c\xf8\xd3\x9eeO\x12')[:32]

    bandersnatch_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(signature))[:32]

    randomness = bytes(SIGNING_CONTEXTS["audit"]) + bandersnatch_proof
    return randomness

print("signature So <=> ", verifiable_random_quality())

hex_value =  ""
print(bytes.fromhex(hex_value))

byte_data = b'00'
hex_string = byte_data.hex()

print(hex_string)  # Output: '68656c6c6f'
