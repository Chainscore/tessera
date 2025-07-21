from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Self

from jam.ring_vrf.curve.e2c import E2C_Variant

from ..glv import DisabledGLV, GLVSpecs
from ..twisted_edwards.te_curve import TECurve
from ..twisted_edwards.te_affine_point import TEAffinePoint


@dataclass(frozen=True)
class JubJubParams:
    """
    JubJub curve parameters.

    Specification of the JubJub curve in Twisted Edwards form.
    """

    SUITE_STRING = b""
    DST = b""

    # Curve parameters
    PRIME_FIELD: Final[
        int
    ] = 0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
    ORDER: Final[
        int
    ] = 0xE7DB4EA6533AFA906673B0101343B00A6682093CCC81082D0970E5ED6F72CB7
    COFACTOR: Final[int] = 8

    # Generator point
    GENERATOR_X: Final[
        int
    ] = 0x11DAFE5D23E1218086A365B99FBF3D3BE72F6AFD7D1F72623E6B071492D1122B
    GENERATOR_Y: Final[
        int
    ] = 0x1D523CF1DDAB1A1793132E78C866C0C33E26BA5CC220FED7CC3F870E59D292AA

    # Edwards curve parameters
    EDWARDS_A: Final[
        int
    ] = 0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000000
    EDWARDS_D: Final[
        int
    ] = 0x2A9318E74BFA2B48F5FD9207E6BD7FD4292D7F6D37579D2601065FD6D6343EB1

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

    # Blinding Base For Pedersen
    BBx: Final[int] = 0x11DAFE5D23E1218086A365B99FBF3D3BE72F6AFD7D1F72623E6B071492D1122B
    BBy: Final[int] = 0x1D523CF1DDAB1A1793132E78C866C0C33E26BA5CC220FED7CC3F870E59D292AA


class JubJubCurve(TECurve):
    """
    Bandersnatch curve implementation.

    A high-performance curve designed for zero-knowledge proofs and VRFs,
    offering both efficiency and security.
    """

    def __init__(self) -> None:
        """Initialize Bandersnatch curve with its parameters."""
        super().__init__(
            PRIME_FIELD=JubJubParams.PRIME_FIELD,
            ORDER=JubJubParams.ORDER,
            GENERATOR_X=JubJubParams.GENERATOR_X,
            GENERATOR_Y=JubJubParams.GENERATOR_Y,
            COFACTOR=JubJubParams.COFACTOR,
            glv=DisabledGLV,
            Z=JubJubParams.Z,
            EdwardsA=JubJubParams.EDWARDS_A,
            EdwardsD=JubJubParams.EDWARDS_D,
            SUITE_STRING=JubJubParams.SUITE_STRING,
            DST=JubJubParams.DST,
            E2C=E2C_Variant.TAI,
            BBx=JubJubParams.BBx,
            BBy=JubJubParams.BBy,
        )


# Singleton instance
JubJub_TE_Curve: Final[JubJubCurve] = JubJubCurve()


@dataclass(frozen=True)
class JubJubPoint(TEAffinePoint):
    """
    Point on the Bandersnatch curve.

    Implements optimized point operations specific to the Bandersnatch curve,
    including GLV scalar multiplication.
    """

    curve: Final[JubJubCurve] = JubJub_TE_Curve

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
        return cls(JubJubParams.GENERATOR_X, JubJubParams.GENERATOR_Y)
