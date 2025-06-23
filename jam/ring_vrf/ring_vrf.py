#create the ring vrf class and put in the signature generation and verification logics
from typing import List

from jam.ring_vrf.ring_proof.ring_vrf_go_tos import*

class RingVrf:

    @staticmethod
    def generate_bls_signature(secret_t,producer_key, keys: List[BandersnatchPublic]):
        """
            get the all the data needed and
            return the signature as an output"
            """
        return generate_bls_signature(secret_t, producer_key, keys)

    @staticmethod
    def construct_ring_root(keys: List[BandersnatchPublic]):
        """
        get the data needed and construct the rng root
        """
        return construct_ring_root(keys)

    @staticmethod
    def verify_signature(message:bytes,ring_root:bytes, ring_signature:bytes):
        """
        get the bls signature, other params if needed and verify it
        """
        return verify_signature(message,ring_root, ring_signature)

    @staticmethod
    def ring_vrf_proof(alpha:bytes, add:bytes, blinding_factor:bytes, producer_key:bytes, keys:List[BandersnatchPublic] ):
        """get the args u want and generate the
        ring_vrf_proof (pedersen vrf proof + ring_proof ) \
        which of length 784 bytes"""
        return ring_vrf_proof(alpha, add, blinding_factor, producer_key, keys)

    @staticmethod
    def ring_vrf_proof_verify(ad_data:bytes, ring_root:bytes, signature:bytes, message=b"")->bool:
        """get the c, r, signature, m and verify the signature"""
        #verfify the signature (pedersen_proof+ring_proof)
        return ring_vrf_proof_verify(ad_data, ring_root, signature)

    @staticmethod
    def pedersen_proof_to_hash(pedersen_proof:bytes):
        """get the pedersen proof alone and return the 32 bytes hash"""
        return pedersen_proof_to_hash(pedersen_proof)

    # pedersen+ring_proof verification

    def ring_vrf_proof_verify(context, ring_root, proof,
                              alpha=b""):  # context(add), ring_root, signature, message(alpha)

        pedersen_proof = proof[:192]
        vrf = PedersenVRF(Bandersnatch_TE_Curve, BandersnatchPoint)
        # get the input point
        input_point = BandersnatchPoint.encode_to_curve(alpha)
        output_point = BandersnatchPoint.string_to_point(pedersen_proof[32 * 0:32 * 1])  # O.p
        rel_to_proove = BandersnatchPoint.string_to_point(pedersen_proof[32 * 1:32 * 2])  # Y'
        R = BandersnatchPoint.string_to_point(pedersen_proof[32 * 2:32 * 3])  # R
        Ok = BandersnatchPoint.string_to_point(pedersen_proof[32 * 3:32 * 4])  # Ok
        S = H.bytes_to_int(pedersen_proof[32 * 4:32 * 5])
        Sb = H.bytes_to_int(pedersen_proof[32 * 5:32 * 6])

        proof_tup = (rel_to_proove, R, Ok, S, Sb)

        # is pedersen proof valid
        p_proof_valid = vrf.verify(
            input_point, context, output_point, proof_tup
        )

        # Extract and verify the Ring proof
        ring_proof = proof[192:]
        proof_ptr = [H.bls_g1_decompress(ring_proof[:48]),
                     H.bls_g1_decompress(ring_proof[48 * 1: 48 * 2]),
                     H.bls_g1_decompress(ring_proof[48 * 2: 48 * 3]),
                     H.bls_g1_decompress(ring_proof[48 * 3:48 * 4]),
                     H.to_scalar_int(ring_proof[48 * 4 + (0 * 32): 48 * 4 + (1 * 32)]),
                     H.to_scalar_int(ring_proof[48 * 4 + (1 * 32): 48 * 4 + (2 * 32)]),
                     H.to_scalar_int(ring_proof[48 * 4 + (2 * 32): 48 * 4 + (3 * 32)]),
                     H.to_scalar_int(ring_proof[48 * 4 + (3 * 32): 48 * 4 + (4 * 32)]),
                     H.to_scalar_int(ring_proof[48 * 4 + (4 * 32): 48 * 4 + (5 * 32)]),
                     H.to_scalar_int(ring_proof[48 * 4 + (5 * 32): 48 * 4 + (6 * 32)]),
                     H.to_scalar_int(ring_proof[48 * 4 + (6 * 32): 48 * 4 + (7 * 32)]),
                     H.bls_g1_decompress(ring_proof[48 * 4 + (7 * 32):(48 * 4) + (7 * 32) + 48]),
                     H.to_scalar_int(ring_proof[(48 * 4) + (7 * 32) + 48: 48 * 4 + (7 * 32) + 48 + 32]),
                     H.bls_g1_decompress(ring_proof[48 * 4 + (7 * 32) + 48 + 32:-48]),
                     H.bls_g1_decompress(ring_proof[-48:])]

        rltn = (rel_to_proove.x, rel_to_proove.y)  # relartion to proove
        res_plus_seed = TwistedEdwardCurve.add(SeedPoint, rltn)
        C_px, C_py, C_s = H.bls_g1_decompress(ring_root[:48]), H.bls_g1_decompress(
            ring_root[48:-48]), H.bls_g1_decompress(
            ring_root[-48:])
        fixed_cols_cmts = [C_px, C_py, C_s]
        verifier_key = {
            'g1': g1_points[0],
            'g2': H.altered_points(g2_points),
            'commitments': [H.to_int(each) for each in H.bls_projective_2_affine(fixed_cols_cmts)]
        }
        valid = Verify(proof_ptr, verifier_key, fixed_cols_cmts, rltn, res_plus_seed, SeedPoint, D)
        # is ring_proof valid
        ring_proof_valid = valid.is_signtaure_valid()
        return p_proof_valid and ring_proof_valid