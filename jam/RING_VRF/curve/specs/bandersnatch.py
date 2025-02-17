from jam.RING_VRF.curve.glv import GLV_Specs
from jam.RING_VRF.curve.twisted_edwards.te_curve import TECurve
from jam.RING_VRF.curve.twisted_edwards.te_affine_point import TEAffinePoint
from jam.RING_VRF.curve.point import Point
from typing import Self

EdwardsA = -5
EdwardsD = 0x6389c12633c267cbc66e3bf86be3b6d8cb66677177e54f92b369f2f5188d58e7
PRIME_FIELD = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001
ORDER = 0x1cfb69d4ca675f520cce760202687600ff8f87007419047174fd06b52876e7e1

GENERATOR = (18886178867200960497001835917649091219057080094937609519140440539760939937304,
             19188667384257783945677642223292697773471335439753913231509108946878080696678)

COFACTOR = 4

# For GLV
lamda = 0x13b4f3dc4a39a493edf849562b38c72bcfc49db970a5056ed13d21408783df05
constant_b = 0x52c9f28b828426a561f00d3a63511a882ea712770d9af4d6ee0f014d172510b4
constant_c = 0x6cc624cf865457c3a97c6efd6c17d1078456abcfff36f4e9515c806cdf650b3d


BandersnatchGLVSpec = GLV_Specs(True, lamda, constant_b, constant_c)

Bandersnatch_TE_Curve = TECurve(PRIME_FIELD, ORDER, GENERATOR[0], GENERATOR[1], COFACTOR, BandersnatchGLVSpec, EdwardsA,
                                EdwardsD)

class BandersnatchPoint(TEAffinePoint):
    def __init__(self, x: int, y: int):
        self.curve = Bandersnatch_TE_Curve
        super().__init__(x, y)

    @classmethod
    def from_mont(cls, p:Point) -> Self:
        return super().from_mont(p, PRIME_FIELD)
