from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, Self

from ..point import Point, PointProtocol
from .te_curve import TECurve

C = TypeVar("C", bound=TECurve)


@dataclass(frozen=True)
class TEAffinePoint(Point[C]):
    """
    Twisted Edwards Curve Point in Affine Coordinates.

    This class implements point operations on a Twisted Edwards curve using affine coordinates.
    Twisted Edwards curves have the form: ax² + y² = 1 + dx²y²

    Attributes:
        x: x-coordinate
        y: y-coordinate
        curve: The Twisted Edwards curve this point belongs to
    """

    def __post_init__(self) -> None:
        """Validate point after initialization."""
        super().__post_init__()
        if not isinstance(self.curve, TECurve):
            raise TypeError("Curve must be a Twisted Edwards curve")

    def is_on_curve(self) -> bool:
        """
        Check if point lies on the Twisted Edwards curve.

        Returns:
            bool: True if point satisfies curve equation
        """
        # ax² + y² = 1 + dx²y²
        v, w = self.x, self.y
        p = self.curve.PRIME_FIELD

        lhs = (self.curve.EdwardsA * pow(v, 2, p) + pow(w, 2, p)) % p
        rhs = (1 + self.curve.EdwardsD * pow(v, 2, p) * pow(w, 2, p)) % p

        return lhs == rhs

    def __add__(self, other: PointProtocol[C]) -> Self:
        """
        Add two points using Twisted Edwards addition formulas.

        Args:
            other: Point to add

        Returns:
            TEAffinePoint: Result of addition

        Raises:
            TypeError: If other is not a TEAffinePoint
        """
        if not isinstance(other, TEAffinePoint):
            raise TypeError("Can only add TEAffinePoints")

        if self == other:
            return self.double()

        if self == self.identity_point():
            return other

        if other == self.identity_point():
            return self

        p = self.curve.PRIME_FIELD
        x1, y1 = self.x, self.y
        x2, y2 = other.x, other.y

        # Compute intermediate values
        x1y2 = (x1 * y2) % p
        x2y1 = (x2 * y1) % p
        y1y2 = (y1 * y2) % p
        x1x2 = (x1 * x2) % p
        dx1x2y1y2 = (self.curve.EdwardsD * x1x2 * y1y2) % p

        # Compute result coordinates
        x3 = ((x1y2 + x2y1) * self.curve.mod_inverse(1 + dx1x2y1y2)) % p
        y3 = (
            (y1y2 - self.curve.EdwardsA * x1x2) * self.curve.mod_inverse(1 - dx1x2y1y2)
        ) % p

        return self.__class__(x3, y3)

    def __neg__(self) -> Self:
        """
        Negate a point.

        Returns:
            TEAffinePoint: Negated point
        """
        return self.__class__(-self.x % self.curve.PRIME_FIELD, self.y)

    def __sub__(self, other: PointProtocol[C]) -> Self:
        """
        Subtract two points.

        Args:
            other: Point to subtract

        Returns:
            TEAffinePoint: Result of subtraction
        """
        return self + (-other)

    def double(self) -> Self:
        """
        Double a point using specialized doubling formulas.

        Returns:
            TEAffinePoint: 2P
        """
        x1, y1 = self.x, self.y
        p = self.curve.PRIME_FIELD

        # Check for identity point
        if y1 == 0:
            return self.identity_point()

        # Calculate denominators
        denom_x = (self.curve.EdwardsA * x1**2 + y1**2) % p
        denom_y = (2 - self.curve.EdwardsA * x1**2 - y1**2) % p

        if denom_x == 0 or denom_y == 0:
            return self.identity_point()

        # Calculate new coordinates
        x3 = (2 * x1 * y1 * self.curve.mod_inverse(denom_x)) % p
        y3 = (
            (y1**2 - self.curve.EdwardsA * x1**2) * self.curve.mod_inverse(denom_y)
        ) % p

        return self.__class__(x3, y3)

    def __mul__(self, scalar: int) -> Self:
        """
        Scalar multiplication using either GLV or double-and-add.

        Args:
            scalar: Integer to multiply by

        Returns:
            TEAffinePoint: Scalar multiplication result
        """
        if self.curve.glv.is_enabled:
            return self.glv_mul(scalar)
        return self.scalar_mul(scalar)

    def scalar_mul(self, scalar: int) -> Self:
        """
        Basic double-and-add scalar multiplication.

        Args:
            scalar: Integer to multiply by

        Returns:
            TEAffinePoint: Scalar multiplication result
        """
        result = self.identity_point()
        addend = self
        scalar = scalar % self.curve.ORDER

        while scalar:
            if scalar & 1:
                result = result + addend
            addend = addend.double()
            scalar >>= 1

        return result

    def glv_mul(self, scalar: int) -> Self:
        """
        GLV scalar multiplication using endomorphism.

        Args:
            scalar: Integer to multiply by

        Returns:
            TEAffinePoint: Scalar multiplication result
        """
        n = self.curve.ORDER
        k1, k2 = self.curve.glv.decompose_scalar(scalar % n, n)
        phi = self.compute_endomorphism()

        return self.scalar_mul(k1) + phi.scalar_mul(k2)

    def compute_endomorphism(self) -> Self:
        """
        Compute the GLV endomorphism of this point.

        Returns:
            TEAffinePoint: Result of endomorphism
        """
        return self.scalar_mul(self.curve.glv.lambda_param)

    def identity_point(self) -> Self:
        """
        Get the identity point (0, 1) of the curve.

        Returns:
            TEAffinePoint: Identity point
        """
        return self.__class__(0, 1)

    @classmethod
    def encode_to_curve(cls, alpha_string: bytes, salt: bytes = b"") -> Self:
        """
        Encode a string to a curve point using Elligator 2.

        Args:
            alpha_string: String to encode
            salt: Optional salt for the encoding

        Returns:
            TEAffinePoint: Resulting curve point
        """
        string_to_hash = salt + alpha_string
        u = cls.curve.hash_to_field(string_to_hash, 2)

        q0 = cls.map_to_curve(u[0])
        q1 = cls.map_to_curve(u[1])
        R = q0 + q1

        return R.clear_cofactor()

    def clear_cofactor(self) -> Self:
        """
        Clear the cofactor to ensure point is in prime-order subgroup.

        Returns:
            TEAffinePoint: Point in prime-order subgroup
        """
        return self.glv_mul(self.curve.COFACTOR)

    @classmethod
    def map_to_curve(cls, u: int) -> Self:
        """
        Map a field element to a curve point using Elligator 2.

        Args:
            u: Field element to map

        Returns:
            TEAffinePoint: Resulting curve point
        """
        s, t = cls.curve.map_to_curve_ell2(u)
        return cls.from_mont(s, t)

    @classmethod
    def from_mont(cls, s: int, t: int) -> Self:
        """
        Convert from Montgomery to Twisted Edwards coordinates.

        Args:
            s: Montgomery s-coordinate
            t: Montgomery t-coordinate

        Returns:
            TEAffinePoint: Point in Twisted Edwards coordinates
        """
        field = cls.curve.PRIME_FIELD

        # Convert coordinates
        tv1 = (s + 1) % field
        tv2 = (tv1 * t) % field

        try:
            tv2 = cls.curve.mod_inverse(tv2)
        except ValueError:
            tv2 = 0

        v = (tv2 * tv1 * s) % field
        w = (tv2 * t * (s - 1)) % field

        # Handle exceptional case
        w = 1 if tv2 == 0 else w

        return cls(v, w)

    @classmethod
    def _x_recover(cls, y: int) -> int:
        """
        Recover x-coordinate from y.
        """
        lhs = 1 - (y ** 2) % cls.curve.PRIME_FIELD
        rhs = cls.curve.EdwardsA - (cls.curve.EdwardsD * (y ** 2)) % cls.curve.PRIME_FIELD
        val = cls.curve.mod_inverse(rhs)
        do_sqrt = lhs * val % cls.curve.PRIME_FIELD
        x = cls.curve.mod_sqrt(do_sqrt) % cls.curve.PRIME_FIELD
        return x
