from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Self

from ..glv import GLVSpecs
from ..twisted_edwards.te_curve import TECurve
from ..twisted_edwards.te_affine_point import TEAffinePoint

@dataclass(frozen=True)
class BandersnatchParams:
    """
    Bandersnatch curve parameters.
    
    The Bandersnatch curve is a Twisted Edwards curve designed for efficient
    implementation of zero-knowledge proofs and VRFs.
    """
    # Curve parameters
    PRIME_FIELD: Final[int] = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001
    ORDER: Final[int] = 0x1cfb69d4ca675f520cce760202687600ff8f87007419047174fd06b52876e7e1
    COFACTOR: Final[int] = 4
    
    # Generator point
    GENERATOR_X: Final[int] = 18886178867200960497001835917649091219057080094937609519140440539760939937304
    GENERATOR_Y: Final[int] = 19188667384257783945677642223292697773471335439753913231509108946878080696678
    
    # Edwards curve parameters
    EDWARDS_A: Final[int] = -5
    EDWARDS_D: Final[int] = 0x6389c12633c267cbc66e3bf86be3b6d8cb66677177e54f92b369f2f5188d58e7
    
    # GLV parameters
    GLV_LAMBDA: Final[int] = 0x13b4f3dc4a39a493edf849562b38c72bcfc49db970a5056ed13d21408783df05
    GLV_B: Final[int] = 0x52c9f28b828426a561f00d3a63511a882ea712770d9af4d6ee0f014d172510b4
    GLV_C: Final[int] = 0x6cc624cf865457c3a97c6efd6c17d1078456abcfff36f4e9515c806cdf650b3d

    # Z
    Z: Final[int] = 5

@dataclass(frozen=True)
class BandersnatchGLVSpecs(GLVSpecs):
    """GLV endomorphism parameters for Bandersnatch curve."""
    is_enabled: Final[bool] = True
    lambda_param: Final[int] = BandersnatchParams.GLV_LAMBDA
    constant_b: Final[int] = BandersnatchParams.GLV_B
    constant_c: Final[int] = BandersnatchParams.GLV_C

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
            glv=BandersnatchGLVSpecs(),
            Z=BandersnatchParams.Z,
            EdwardsA=BandersnatchParams.EDWARDS_A,
            EdwardsD=BandersnatchParams.EDWARDS_D
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
        return cls(
            BandersnatchParams.GENERATOR_X,
            BandersnatchParams.GENERATOR_Y
        )
    
    def to_bytes(self) -> bytes:
        """
        Convert point to compressed byte representation.
        
        Returns:
            bytes: Compressed point representation
        """
        return self.point_to_string()
    
    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        """
        Create point from compressed byte representation.
        
        Args:
            data: Compressed point bytes
            
        Returns:
            BandersnatchPoint: Decoded point
            
        Raises:
            ValueError: If data is invalid
        """
        return cls.string_to_point(data)