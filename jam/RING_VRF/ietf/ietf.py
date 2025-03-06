
from jam.RING_VRF.vrf import VRF
from jam.RING_VRF.curve.specs.bandersnatch import Bandersnatch_TE_Curve
from typing import Tuple
from dataclasses import  dataclass
@dataclass
class IETF_VRF(VRF):
    curve = Bandersnatch_TE_Curve


    def proof(self, alpha, secret_key,additional_data):
        input_point = self.curve.encode_to_curve(alpha)
        O = secret_key* input_point
        Y = secret_key* (self.curve.GENERATOR_X,self.curve.GENERATOR_Y)
        # print("Inside Generate Proof: Op-H",Utilities.point_to_string(O).hex())
        # print("Inside generate Proof:Public Key-PK",Utilities.point_to_string(Y).hex()
        # print("y_normal:",Y)
        # y_g = Curve.TwistedEdwardCurve.mul_by_glv(secret_key, constants.GENERATOR)
        # print("y_glv:",y_g)
        k = VRF.generate_nonce(secret_key, input_point)
        U, V = k* (self.curve.GENERATOR_X,self.curve.GENERATOR_Y), k*input_point
        c = VRF.challenge(Y, input_point, O, U, V, additional_data)
        s = (k + c * secret_key) % self.curve.ORDER
        return O, (c, s)


    def verify(self,public_key: Tuple[int, int], input_point: Tuple[int, int],additional_data:bytes, output_point: Tuple[int, int],proof: Tuple[int, int]) -> bool:
        """Verify a VRF ticket"""

        c, s = proof
        U = s* (self.curve.GENERATOR_Y, self.curve.GENERATOR_Y) - c* public_key
        V = s* input_point - c*output_point
        return c == VRF.challenge(public_key, input_point, output_point, U, V, additional_data)



ietf_vrf = IETF_VRF(Bandersnatch_TE_Curve.PRIME_FIELD,Bandersnatch_TE_Curve.COFACTOR,Bandersnatch_TE_Curve.GENERATOR_X,Bandersnatch_TE_Curve.GENERATOR_Y,Bandersnatch_TE_Curve.ORDER,Bandersnatch_TE_Curve.glv)

