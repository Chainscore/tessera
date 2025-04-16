from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Self

from ..glv import DisabledGLV
from ..twisted_edwards.te_curve import TECurve
from ..twisted_edwards.te_affine_point import TEAffinePoint

@dataclass(frozen=True)
class BabyJubJubParams:
    """
    Baby JubJub curve parameters.
    
    Specification of the Baby JubJub curve in Twisted Edwards form.
    """
    SUITE_STRING=b""
    DST=b""

    # Curve parameters
    PRIME_FIELD: Final[int] = 21888242871839275222246405745257275088548364400416034343698204186575808495617
    ORDER: Final[int] = 273603115188753742007522749811879420859037173
    COFACTOR: Final[int] = 8
    
    # Generator point
    GENERATOR_X: Final[int] = 995203441582195749578291179787384436505546430278305826713579947235728471134
    GENERATOR_Y: Final[int] = 5472060717959818805561601436314318772137091100104008585924551046643952123905
    
    # Edwards curve parameters
    EDWARDS_A: Final[int] = 168700
    EDWARDS_D: Final[int] = 168696
    
    GLV_LAMBDA: Final[int] = 0
    GLV_B: Final[int] = 0
    GLV_C: Final[int] = 0

    # Z
    Z: Final[int] = 5

class BabyJubJubCurve(TECurve):
    """
    Bandersnatch curve implementation.
    
    A high-performance curve designed for zero-knowledge proofs and VRFs,
    offering both efficiency and security.
    """
    def __init__(self) -> None:
        """Initialize Bandersnatch curve with its parameters."""
        super().__init__(
            PRIME_FIELD=BabyJubJubParams.PRIME_FIELD,
            ORDER=BabyJubJubParams.ORDER,
            GENERATOR_X=BabyJubJubParams.GENERATOR_X,
            GENERATOR_Y=BabyJubJubParams.GENERATOR_Y,
            COFACTOR=BabyJubJubParams.COFACTOR,
            glv=DisabledGLV,
            Z=BabyJubJubParams.Z,
            EdwardsA=BabyJubJubParams.EDWARDS_A,
            EdwardsD=BabyJubJubParams.EDWARDS_D,
            SUITE_STRING=BabyJubJubParams.SUITE_STRING,
            DST=BabyJubJubParams.DST
        )

# Singleton instance
BabyJubJub_TE_Curve: Final[BabyJubJubParams] = BabyJubJubCurve()

@dataclass(frozen=True)
class BabyJubJubPoint(TEAffinePoint):
    """
    Point on the Bandersnatch curve.
    
    Implements optimized point operations specific to the Bandersnatch curve,
    including GLV scalar multiplication.
    """
    curve: Final[BabyJubJubCurve] = BabyJubJub_TE_Curve
    
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
            BabyJubJubParams.GENERATOR_X % BabyJubJubParams.PRIME_FIELD,
            BabyJubJubParams.GENERATOR_Y % BabyJubJubParams.PRIME_FIELD
        )