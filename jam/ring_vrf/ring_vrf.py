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
        #secret_t(Bytearray32), producer_key(BandernstachKey)
        # signature = func() #make the call or logic u want
        # return signature
        return generate_bls_signature(secret_t, producer_key, keys)

    @staticmethod
    def construct_ring_root(keys: List[BandersnatchPublic]):
        """
        get the data needed and construct the rng root
        """
        #
        # ring_root= func() make the call ore logic u want
        # return ring_root
        return construct_ring_root(keys)

    @staticmethod
    def verify_signature(message, ring_signature):
        """
        get the bls signature, other params if needed and verify it
        """
        # is_valid=func() # make the func call or logic u want
        # return is_valid
        return verify_signature(message, ring_signature)

    @staticmethod
    def ring_vrf_proof(alpha, add, blinding_factor, producer_key, keys:List[BandersnatchPublic] ):
        """get the args u want and generate the
        ring_vrf_proof (pedersen vrf proof + ring_proof ) \
        which of length 784 bytes"""

        # pedersen_proof=get the pedersen proof
        # ring_proof= get the ring proof
        # rvrf_proof= add the pedersen and ring proof
        # return rvrf_proof
        return ring_vrf_proof(alpha, add, blinding_factor, producer_key, keys)

    @staticmethod
    def pedersen_proof_to_hash(pedersen_proof):
        """get the pedersen proof alone and return the 32 bytes hash"""
        return pedersen_proof_to_hash(pedersen_proof)









