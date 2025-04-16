from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Self

from ..glv import DisabledGLV
from ..twisted_edwards.te_curve import TECurve
from ..twisted_edwards.te_affine_point import TEAffinePoint

@dataclass(frozen=True)
class JubJubParams:
    """
    JubJub curve parameters.
    
    Specification of the JubJub curve in Twisted Edwards form.
    """
    SUITE_STRING=b""
    DST=b""

    # Curve parameters
    PRIME_FIELD: Final[int] = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001
    ORDER: Final[int] = 0xe7db4ea6533afa906673b0101343b00a6682093ccc81082d0970e5ed6f72cb7
    COFACTOR: Final[int] = 8
    
    # Generator point
    GENERATOR_X: Final[int] = 0x11dafe5d23e1218086a365b99fbf3d3be72f6afd7d1f72623e6b071492d1122b
    GENERATOR_Y: Final[int] = 0x1d523cf1ddab1a1793132e78c866c0c33e26ba5cc220fed7cc3f870e59d292aa
    
    # Edwards curve parameters
    EDWARDS_A: Final[int] = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000000
    EDWARDS_D: Final[int] = 0x2a9318e74bfa2b48f5fd9207e6bd7fd4292d7f6d37579d2601065fd6d6343eb1
    
    GLV_LAMBDA: Final[int] = 0
    GLV_B: Final[int] = 0
    GLV_C: Final[int] = 0

    # Z
    Z: Final[int] = 5

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
            DST=JubJubParams.DST
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
        return cls(
            JubJubParams.GENERATOR_X,
            JubJubParams.GENERATOR_Y
        )