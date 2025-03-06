from jam.RING_VRF.curve.specs.bandersnatch import Bandersnatch_TE_Curve

from jam.RING_VRF.vrf import VRF
from dataclasses import  dataclass
@dataclass
class PedersenVRF(VRF):
    # Blinding Base For Pedersen
    BBx = 14576224270591906826192118712803723445031237947873156025406837473427562701854
    BBy = 38436873314098705092845609371301773715650206984323659492499960072785679638442
    B_BASE = (BBx, BBy)
    BB_compressed = 0xaa5f60f3b3126fa406972d2023ee03bf281022209d13882199113619d57ffa54
    curve=Bandersnatch_TE_Curve

    @staticmethod
    def proof(secret_key: int, blinding_factor: int, alpha_string, ad:bytes):

        """Generate a VRF ticket."""
        input_point=PedersenVRF.curve.encode_to_curve(alpha_string)
        O = secret_key*input_point
        k = VRF.generate_nonce(secret_key, input_point)
        Kb = VRF.generate_nonce(blinding_factor, input_point)
        Y = secret_key*(PedersenVRF.curve.GENERATOR_X,PedersenVRF.curve.GENERATOR_Y) + blinding_factor* PedersenVRF.B_BASE
        R = k*(PedersenVRF.curve.GENERATOR_X,PedersenVRF.curve.GENERATOR_Y) + Kb *PedersenVRF.B_BASE
        Ok = k * input_point
        c = VRF.challenge(Y, input_point, O, R, Ok, ad)
        s = (k + c * secret_key) % PedersenVRF.curve.ORDER
        Sb = (Kb + c * blinding_factor) % PedersenVRF.curve.ORDER

        return O, (Y, R, Ok, s, Sb)


    @staticmethod
    def verify(input_point, ad, output_point, proof):
        """Verify a VRF ticket."""
        Y, R, Ok, s, Sb = proof
        c = VRF.challenge(Y, input_point, output_point, R, Ok, ad)
        Theta0 = (Ok + c*output_point) == s* input_point
        Theta1 = R+ (c*Y) ==s*(PedersenVRF.curve.GENERATOR_X,PedersenVRF.curve.GENERATOR_Y) +Sb * PedersenVRF.B_BASE

        return Theta0 == Theta1

