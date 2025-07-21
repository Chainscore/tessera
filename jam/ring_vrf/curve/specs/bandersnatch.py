from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Self

from jam.ring_vrf.curve.e2c import E2C_Variant

from ..glv import DisabledGLV, GLVSpecs
from ..twisted_edwards.te_curve import TECurve
from ..twisted_edwards.te_affine_point import TEAffinePoint


@dataclass(frozen=True)
class BandersnatchParams:
    """
    Bandersnatch curve parameters.

    The Bandersnatch curve is a Twisted Edwards curve designed for efficient
    implementation of zero-knowledge proofs and VRFs.
    """

    SUITE_STRING = b"Bandersnatch_SHA-512_ELL2"
    DST = b"ECVRF_Bandersnatch_XMD:SHA-512_ELL2_RO_Bandersnatch_SHA-512_ELL2"

    # Curve parameters
    PRIME_FIELD: Final[
        int
    ] = 0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
    ORDER: Final[
        int
    ] = 0x1CFB69D4CA675F520CCE760202687600FF8F87007419047174FD06B52876E7E1
    COFACTOR: Final[int] = 4

    # Generator point
    GENERATOR_X: Final[
        int
    ] = 18886178867200960497001835917649091219057080094937609519140440539760939937304
    GENERATOR_Y: Final[
        int
    ] = 19188667384257783945677642223292697773471335439753913231509108946878080696678

    # Edwards curve parameters
    EDWARDS_A: Final[int] = -5
    EDWARDS_D: Final[
        int
    ] = 0x6389C12633C267CBC66E3BF86BE3B6D8CB66677177E54F92B369F2F5188D58E7

    # GLV parameters
    GLV_LAMBDA: Final[
        int
    ] = 0x13B4F3DC4A39A493EDF849562B38C72BCFC49DB970A5056ED13D21408783DF05
    GLV_B: Final[
        int
    ] = 0x52C9F28B828426A561F00D3A63511A882EA712770D9AF4D6EE0F014D172510B4
    GLV_C: Final[
        int
    ] = 0x6CC624CF865457C3A97C6EFD6C17D1078456ABCFFF36F4E9515C806CDF650B3D

    # Z
    Z: Final[int] = 5

    # Blinding Base For Pedersen (old)
    # BBx: Final[
    #     int
    # ] = 14576224270591906826192118712803723445031237947873156025406837473427562701854
    # BBy: Final[
    #     int
    # ] = 38436873314098705092845609371301773715650206984323659492499960072785679638442

    # new
    BBx: Final[
        int
    ] = 6150229251051246713677296363717454238956877613358614224171740096471278798312
    BBy: Final[
        int
    ] = 28442734166467795856797249030329035618871580593056783094884474814923353898473


"""GLV endomorphism parameters for Bandersnatch curve."""
BandersnatchGLVSpecs = GLVSpecs(
    is_enabled=True,
    lambda_param=BandersnatchParams.GLV_LAMBDA,
    constant_b=BandersnatchParams.GLV_B,
    constant_c=BandersnatchParams.GLV_C,
)


class BandersnatchCurve(TECurve):
    """
    Bandersnatch curve implementation.

    A high-performance curve designed for zero-knowledge proofs and VRFs,
    offering both efficiency and security.
    """

    def __init__(self) -> None:
        """Initialize Bandersnatch curve with its parameters."""
        super().__init__(
            PRIME_FIELD=BandersnatchParams.PRIME_FIELD,
            ORDER=BandersnatchParams.ORDER,
            GENERATOR_X=BandersnatchParams.GENERATOR_X,
            GENERATOR_Y=BandersnatchParams.GENERATOR_Y,
            COFACTOR=BandersnatchParams.COFACTOR,
            glv=BandersnatchGLVSpecs,
            Z=BandersnatchParams.Z,
            EdwardsA=BandersnatchParams.EDWARDS_A,
            EdwardsD=BandersnatchParams.EDWARDS_D,
            SUITE_STRING=BandersnatchParams.SUITE_STRING,
            DST=BandersnatchParams.DST,
            E2C=E2C_Variant.ELL2,
            BBx=BandersnatchParams.BBx,
            BBy=BandersnatchParams.BBy,
        )


# Singleton instance
Bandersnatch_TE_Curve: Final[BandersnatchCurve] = BandersnatchCurve()


@dataclass(frozen=True)
class BandersnatchPoint(TEAffinePoint):
    """
    Point on the Bandersnatch curve.

    Implements optimized point operations specific to the Bandersnatch curve,
    including GLV scalar multiplication.
    """

    curve: Final[BandersnatchCurve] = Bandersnatch_TE_Curve

    def __init__(self, x: int, y: int) -> None:
        """
        Initialize a point on the Bandersnatch curve.

        Args:
            x: x-coordinate
            y: y-coordinate

        Raises:
            ValueError: If point is not on curve
        """
        super().__init__(x, y, self.curve)

    @classmethod
    def generator_point(cls) -> Self:
        """
        Get the generator point of the curve.

        Returns:
            BandersnatchPoint: Generator point
        """
        return cls(BandersnatchParams.GENERATOR_X, BandersnatchParams.GENERATOR_Y)
