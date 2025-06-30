from typing import Optional, Tuple, List
from tsrkit_types import Bytes, TypedVector, U32, Null
# from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint, Bandersnatch_TE_Curve
# from jam.types.work.report import WorkReport
# from jam.utils.constants import SIGNING_CONTEXTS
# from jam.types.protocol.crypto import Hash, BandersnatchPublic
# from jam.ring_vrf.ietf.ietf import IETF_VRF
# from jam.types.block.header import Header
# from jam.types import BandersnatchVrfSignature
# from jam.utils.shuffle import shuffle
# from jam.types.protocol.core import CoreIndex
#
#
# def vrf_signature_bandersnatch(entropy_source: BandersnatchVrfSignature, bandersnatch_key: BandersnatchPublic, tranche_index: int = None, w_report: Optional[WorkReport] = None) -> Bytes[96]:
#     print("entropy_source => ", entropy_source)
#     print("bandersnatch_key => ", bandersnatch_key)
#
#     vrf = IETF_VRF(Bandersnatch_TE_Curve, BandersnatchPoint)
#
#     entropy_vrf_proof = vrf.proof_to_hash(BandersnatchPoint.encode_to_curve(entropy_source.encode()))[:32]
#     print("entropy_vrf_proof => ", entropy_vrf_proof)
#
#     random_quantity = bytes(SIGNING_CONTEXTS["audit"]) + entropy_vrf_proof  # Xv + y(Hv)
#     print("random_quantity => ", random_quantity)
#
#     key = int.from_bytes(bytes.fromhex(str(bandersnatch_key)))
#     print("key =>", key)
#
#     output_point, proof = vrf.prove(alpha=b"", secret_key=key, additional_data=random_quantity, salt=b"")
#     print("output_point =>", output_point)
#     op_bt_str = output_point.point_to_string()
#     print("op_bt_str =>", op_bt_str)
#     print("proof 1&2", proof)
#
#     proof_bt_str = proof[0].to_bytes(32,'little') + proof[1].to_bytes(32, 'little')
#     signature = op_bt_str + proof_bt_str  # Expected S0 (96bytes)
#
#     if tranche_index is not None and tranche_index > 0 and w_report is not None:
#         random_quantity += bytes(Hash.blake2b(w_report.encode()).encode()) + bytes(tranche_index)  # refer 17.15
#
#     # F Function needs to be implemented Here expected to return [sets of signatures]
#
#     return signature
#
# randomness  = vrf_signature_bandersnatch(
#     entropy_source= "f7caffd3498473b08ab9de28ba3bd76d94f3fe47acc96e6e0111dfe301ba4d0bc7b3a95ebf21a76fb76102c13fdf9947c6c243d71b9893fae0b9adf94aa83f0a81b4566c15c796a79a4e124971130cba959c03066efba2161334cedc0d02151a",
#     bandersnatch_key= "ff71c6c03ff88adb5ed52c9681de1629a54e702fc14729f6b50d2f0a76f185b3"
# )
#
# # print("ye rha hmara s_o", randomness.hex())
#
#
# dummy_array : TypedVector[U32] = [1, 2, 3, 4 , 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 ,15, 16, 17, 18, 19, 20]
#
# signature = "6d1dd583bea262323c7dc9e94e57a472e09874e435719010eeafae503c433f16" + "6dbeeab9648505fa6a95de52d611acfbb2febacc58cdc7d0ca45abd8c952ef12" + "ce7f4a2354a6c3f97aee6cc60c6aa4c4430b12ed0f0ef304b326c776618d7609"
#
# shuffled_aray = shuffle(h="777bcc9cc655838fd28c223ce459060bf6bccd1e081ed11cc19fdddc46a978639aa298f678112cb4e8c15386f6414a841d10b487f465faf31c2c515e07ca4c0424c763a274bc12202ffc9e493a90cfbdb0623cc593f15a47c2571047d40d0802", array= dummy_array)
# print("hello")
# print(shuffled_aray)


# def vrs_func(self, header: Header, state: state) -> List[Tuple[CoreIndex, WorkReport]]:
#     """
#     This function give the non-empty-item to audit through a verifiable random selection of ten cores:
#
#     Sources:
#         https://graypaper.fluffylabs.dev/#/9a08063/1ebc001e1701?v=0.6.6
#
#     Equations:
#         17.7 r = y(So)
#         17.6 p = f([(c, Qc) | c <- Nc ], r )
#         17.5 ao = {(c, w) | (c, w) E p... + 10, w != Phi }



# ---------------------------------------------- Dummy data ------------------------------------------------------------
# a =  AuditingAndJudgement()

# print("vrf_signature_bandersnatch => ",a.vrf_signature_bandersnatch( entropy_source="f7caffd3498473b08ab9de28ba3bd76d94f3fe47acc96e6e0111dfe301ba4d0bc7b3a95ebf21a76fb76102c13fdf9947c6c243d71b9893fae0b9adf94aa83f0a81b4566c15c796a79a4e124971130cba959c03066efba2161334cedc0d02151a",
#         bandersnatch_key="ff71c6c03ff88adb5ed52c9681de1629a54e702fc14729f6b50d2f0a76f185b3").hex())

# shuffle = shuffle(h="777bcc9cc655838fd28c223ce459060bf6bccd1e081ed11cc19fdddc46a978639aa298f678112cb4e8c15386f6414a841d10b487f465faf31c2c515e07ca4c0424c763a274bc12202ffc9e493a90cfbdb0623cc593f15a47c2571047d40d0802", array=dummy_array)
# print("Shuffle based on the first function output =>  ", shuffle)


print(a.vrs_func(entropy_source="f7caffd3498473b08ab9de28ba3bd76d94f3fe47acc96e6e0111dfe301ba4d0bc7b3a95ebf21a76fb76102c13fdf9947c6c243d71b9893fae0b9adf94aa83f0a81b4566c15c796a79a4e124971130cba959c03066efba2161334cedc0d02151a",
        bandersnatch_key="ff71c6c03ff88adb5ed52c9681de1629a54e702fc14729f6b50d2f0a76f185b3"))











