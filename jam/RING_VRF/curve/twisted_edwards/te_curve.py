from __future__ import annotations

from dataclasses import dataclass
from typing import Final, TypeVar

from jam.ring_vrf.curve.curve import Curve, CurveProtocol

T = TypeVar('T', bound='TECurve')

class TECurveProtocol(CurveProtocol):
    """Protocol defining the interface for Twisted Edwards curves."""
    EdwardsA: int
    EdwardsD: int

@dataclass(frozen=True)
class TECurve(Curve):
    """
    Twisted Edwards Curve implementation.
    
    A Twisted Edwards curve is defined by the equation:
    ax² + y² = 1 + dx²y²
    
    where a, d are distinct, non-zero elements of the field.
    
    Attributes:
        EdwardsA: The 'a' parameter in the curve equation
        EdwardsD: The 'd' parameter in the curve equation
    """
    EdwardsA: Final[int]
    EdwardsD: Final[int]
    
    def __post_init__(self) -> None:
        """Validate curve parameters after initialization."""
        super().__post_init__()
        if not self._validate_edwards_params():
            raise ValueError("Invalid Twisted Edwards curve parameters")
    
    def _validate_edwards_params(self) -> bool:
        """
        Validate Twisted Edwards specific parameters.
        
        Returns:
            bool: True if parameters are valid
        """
        return (
            self.EdwardsA != 0 and
            self.EdwardsD != 0 and
            self.EdwardsA != self.EdwardsD and
            all(x < self.PRIME_FIELD for x in (self.EdwardsA, self.EdwardsD))
        )
    
    @property
    def curve_equation(self) -> str:
        """
        Get the curve equation in readable form.
        
        Returns:
            str: Curve equation
        """
        return f"{self.EdwardsA}x² + y² = 1 + {self.EdwardsD}x²y²"
    
    def is_complete(self) -> bool:
        """
        Check if the curve is complete.
        
        A Twisted Edwards curve is complete if:
        - a is square
        - d is non-square
        in the base field.
        
        Returns:
            bool: True if curve is complete
        """
        return (
            self.is_square(self.EdwardsA) and
            not self.is_square(self.EdwardsD)
        )