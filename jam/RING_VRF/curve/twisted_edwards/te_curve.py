from dataclasses import dataclass
from jam.RING_VRF.curve.curve import  Curve

@dataclass
class TECurve(Curve):
    EdwardsA: int
    EdwardsD: int

    # def map_to_curve(self, u):  #defined in te_affine_point
    #     p = self.map_to_curve_ell2(u)
    #     tep = self.from_mont(p)
    #     return tep




