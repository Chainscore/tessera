
from jam.ring_vrf.vrf import VRF
from jam.ring_vrf.curve.specs.bandersnatch import Bandersnatch_TE_Curve
from typing import Tuple
from jam.ring_vrf.curve.specs.bandersnatch import BandersnatchPoint
from jam.ring_vrf.curve.curve import Curve

class IETF_VRF(VRF):
    curve: Curve

    def __init__(self, curve: Curve):
        self.curve = curve

    def proof(self, alpha: bytes, secret_key: int, additional_data: bytes, salt: bytes = b'') -> Tuple[BandersnatchPoint, Tuple[int, int]]:
        """Produce a VRF proof"""
        generator = BandersnatchPoint(self.curve.GENERATOR_X, self.curve.GENERATOR_Y)
        
        # Encode input octet-string to a curve point using Elligator-2
        input_point = generator.encode_to_curve(alpha, salt)
        print("input_point", input_point.x, input_point.y)
        
        # Compute output point and public key
        output_point = input_point * secret_key
        public_key = generator * secret_key
        
        # Generate deterministic nonce
        nonce = self.generate_nonce(secret_key, input_point)
        
        # Compute U = k*G and V = k*I
        U = generator * nonce
        V = input_point * nonce
        
        # Compute challenge c
        c = self.challenge(public_key, input_point, output_point, U, V, additional_data)
        
        # Compute proof components
        s = (nonce + c * secret_key) % self.curve.ORDER
        
        return output_point, (c, s)

    def verify(self,public_key: Tuple[int, int], input_point: Tuple[int, int],additional_data:bytes, output_point: Tuple[int, int],proof: Tuple[int, int]) -> bool:
        """Verify a VRF ticket"""

        c, s = proof
        U = s* (self.curve.GENERATOR_Y, self.curve.GENERATOR_Y) - c* public_key
        V = s* input_point - c*output_point
        return c == VRF.challenge(public_key, input_point, output_point, U, V, additional_data)



# ietf_vrf = IETF_VRF(Bandersnatch_TE_Curve.PRIME_FIELD,Bandersnatch_TE_Curve.COFACTOR,Bandersnatch_TE_Curve.GENERATOR_X,Bandersnatch_TE_Curve.GENERATOR_Y,Bandersnatch_TE_Curve.ORDER,Bandersnatch_TE_Curve.glv)

