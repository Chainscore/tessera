from jam.ring_vrf.curve.curve import  Curve
from jam.ring_vrf.curve.glv import GLV_Specs

class TECurve(Curve):
    EdwardsA: int
    EdwardsD: int

    def __init__(self, prime_field: int, order: int, generator_x: int, generator_y: int, cofactor: int, glv: GLV_Specs, EdwardsA: int, EdwardsD: int):
        super().__init__(prime_field, order, generator_x, generator_y, cofactor, glv)
        self.EdwardsA = EdwardsA
        self.EdwardsD = EdwardsD


    # def map_to_curve(self, u):  #defined in te_affine_point
    #     p = self.map_to_curve_ell2(u)
    #     tep = self.from_mont(p)
    #     return tep




