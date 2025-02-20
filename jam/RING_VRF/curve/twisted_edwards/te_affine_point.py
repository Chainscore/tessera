from jam.RING_VRF.curve.twisted_edwards.te_curve import TECurve
from jam.RING_VRF.curve.point import Point
from typing import Tuple
from typing import Self

class TEAffinePoint(Point):
    curve: TECurve

    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        if not self.is_on_curve():
            raise AssertionError

    def __mul__(self, other: int) -> Point:
        if self.curve.glv.is_glv:
            return self.glv_mul(other)
        return self.scalar_mul(other)


    def identity_point(self)->Self:
        return self.__class__(0,1)

    def scalar_mul(self, other: int) -> Self:
        result = self.identity_point()
        addend = self
        while other:
            if other & 1:
                result = result + addend
            addend = addend.double()
            other >>= 1
        
        return result


    def __add__(self, other: Point) -> Self:
        x1, y1 = self.x, self.y
        x2, y2 = other.x, other.y
        if self == other:
            return self.double()
        if self == self.identity_point():
            return other
        if other == self.identity_point():
            return self

        x1y2 = (x1 * y2) % self.curve.PRIME_FIELD
        x2y1 = (x2 * y1) % self.curve.PRIME_FIELD
        y1y2 = (y1 * y2) % self.curve.PRIME_FIELD
        x1x2 = (x1 * x2) % self.curve.PRIME_FIELD
        dx1x2y1y2 = (self.curve.EdwardsD * x1x2 * y1y2) % self.curve.PRIME_FIELD

        x3 = ((x1y2 + x2y1) * self.mod_inverse(1 + dx1x2y1y2, self.curve.PRIME_FIELD)) % self.curve.PRIME_FIELD
        y3 = ((y1y2 - self.curve.EdwardsA * x1x2) * self.mod_inverse(1 - dx1x2y1y2, self.curve.PRIME_FIELD)) % self.curve.PRIME_FIELD

        return self.__class__(x3, y3)

    def __neg__(self)->Self:
        self.x = -self.x % self.curve.PRIME_FIELD
        return self

    def __sub__(self,other:Point)->Self:
        return self + ~other


    def double(self)->Self:
        x1, y1 = self.x, self.y

        # Check if the point is at infinity (identity element)
        if y1 == 0:
            return self.identity_point()  # Return the identity point in twisted Edwards form

        # Calculate new coordinates using the doubling formula
        denom_x = (self.curve.EdwardsA * x1 ** 2 + y1 ** 2) % self.curve.PRIME_FIELD
        denom_y = (2 - self.curve.EdwardsA * x1 ** 2 - y1 ** 2) % self.curve.PRIME_FIELD
        if denom_x == 0 or denom_y == 0:
            return self.identity_point()  # Return identity if denominator is zero

        x3 = (2 * x1 * y1 * self.mod_inverse(denom_x, self.curve.PRIME_FIELD)) % self.curve.PRIME_FIELD
        y3 = ((y1 ** 2 - self.curve.EdwardsA * x1 ** 2) * self.mod_inverse(denom_y, self.curve.PRIME_FIELD)) % self.curve.PRIME_FIELD

        return self.__class__(x3, y3)

    @staticmethod
    def mod_inverse(val: int, field: int) -> int:
        """Finds the Mod Inverse Using Fermat's little Theorem"""

        if pow(val, field - 1, field) != 1:
            raise ValueError("No inverse exists")
        return pow(val, field - 2, field)


    #shuld we call the encode to curve here
    def encode_to_curve(self, alpha_string: str, encode_to_curve_salt="") -> Point:
        string_to_be_hashed = alpha_string + encode_to_curve_salt
        u = self.curve.hash_to_field(string_to_be_hashed, 2)

        q0 = self.map_to_curve(u[0])
        q1 = self.map_to_curve(u[1])
        R = q0 + q1
        p = R.clear_cofactor()
        return p

    def clear_cofactor(self)-> Self:
        """ Helps to convert the point to be on the Edwards Curve"""

        return self.glv_mul(self.curve.COFACTOR)


    def map_to_curve(self, u):  # defined in te_affine_point

        p = self.map_to_curve_ell2(u)
        tep = self.from_mont(p)
        return tep


    @classmethod
    def from_mont(cls, p:Point, field: int) -> Self:
        (s, t) = (p.x, p.y)
        # 1. tv1 = s + 1
        tv1 = (s + 1) % field

        # 2. tv2 = tv1 * t        # (s + 1) * t
        tv2 = (tv1 * t) % field

        # 3. tv2 = inv0(tv2)      # 1 / ((s + 1) * t)
        try:
            tv2 = cls.mod_inverse(tv2, field)
        except ValueError:
            tv2 = 0  # Handle the exceptional case where inverse doesn't exist

        # 4. v = tv2 * tv1        # 1 / t
        v = (tv2 * tv1) % field

        # 5. v = v * s            # s / t
        v = (v * s) % field

        # 6. w = tv2 * t          # 1 / (s + 1)
        w = (tv2 * t) % field

        # 7. tv1 = s - 1
        tv1 = (s - 1) % field

        # 8. w = w * tv1          # (s - 1) / (s + 1)
        w = (w * tv1) % field

        # 9. e = tv2 == 0
        e = tv2 == 0

        # 10. w = CMOV(w, 1, e)   # handle exceptional case
        w = 1 if e else w

        # 11. return (v, w)
        return cls(v,w)


    def is_on_curve(self) -> bool:
        v, w = self.x, self.y
        lhs = (self.curve.EdwardsA * pow(v, 2, self.curve.PRIME_FIELD) + pow(w, 2,self.curve.PRIME_FIELD)) % self.curve.PRIME_FIELD
        rhs = (1 + self.curve.EdwardsD * pow(v, 2, self.curve.PRIME_FIELD) * pow(w, 2,self.curve.PRIME_FIELD)) % self.curve.PRIME_FIELD
        return lhs == rhs

    def _x_recover(self, y:int)->int:
        """Recover the x coordinate from the y coordinate."""
        lhs = 1 - (y ** 2) % self.curve.PRIME_FIELD
        rhs = self.curve.EdwardsA - (self.curve.EdwardsD * (y ** 2)) % self.curve.PRIME_FIELD
        val = self.mod_inverse(rhs, self.curve.PRIME_FIELD)
        do_sqrt = lhs * val % self.curve.PRIME_FIELD
        x = self.curve.mod_sqrt(do_sqrt) % self.curve.PRIME_FIELD
        return x


    def calculate_j_k(self) -> Tuple[int, int]:
        # J = 2(a + d)/(a - d)
        # K = 4/(a - d)
        denom = (self.curve.EdwardsA - self.curve.EdwardsD) % self.curve.PRIME_FIELD
        denom_inv = self.mod_inverse(denom)

        J = (2 * (self.curve.EdwardsA + self.curve.EdwardsD) * denom_inv) % self.curve.PRIME_FIELD
        K = (4 * denom_inv) % self.curve.PRIME_FIELD
        return J, K

    def map_to_curve_ell2(self, u:int) -> Point:
        """
        Args:
            u:
        Returns:
            Point on Montgomery Curve
        """
        J,K=self.calculate_j_k()
        Z=self.curve.find_z_ell2()

        c1 = (J * self.mod_inverse(K)) % self.curve.PRIME_FIELD
        c2 = self.mod_inverse(pow(K, 2, self.curve.PRIME_FIELD)) % self.curve.PRIME_FIELD

        # Step 1-2: Compute tv1 = Z * u^2
        tv1 = pow(u, 2, self.curve.PRIME_FIELD)  # u^2
        tv1 = (Z * tv1) % self.curve.PRIME_FIELD

        # Step 3-4: Handle exceptional case
        e1 = (tv1 == -1)  # Check if tv1 == -1
        tv1 = self.curve.CMOV(tv1, 0, e1)  # If tv1 == -1, set tv1 = 0

        # Step 5-7: Compute x1
        x1 = (tv1 + 1) % self.curve.PRIME_FIELD
        x1 = self.mod_inverse(x1)
        x1 = (-c1 * x1) % self.curve.PRIME_FIELD  # x1 = -(J / K) / (1 + Z * u^2)

        # Step 8-11: Compute gx1
        gx1 = (x1 + c1) % self.curve.PRIME_FIELD
        gx1 = (gx1 * x1) % self.curve.PRIME_FIELD
        gx1 = (gx1 + c2) % self.curve.PRIME_FIELD
        gx1 = (gx1 * x1) % self.curve.PRIME_FIELD  # gx1 = x1^3 + (J / K) * x1^2 + x1 / K^2

        # Step 12: Compute x2
        x2 = (-x1 - c1) % self.curve.PRIME_FIELD

        # Step 13: Compute gx2
        gx2 = (tv1 * gx1) % self.curve.PRIME_FIELD

        # Step 14-16: Choose x and y2 based on gx1 square test
        e2 = self.curve.is_square(gx1)
        x = self.curve.CMOV(x2, x1, e2)  # If is_square(gx1), choose x1; else choose x2
        y2 = self.curve.CMOV(gx2, gx1, e2)

        # Step 17: Compute sqrt(y2) with fallback for non-square cases
        y = self.curve.mod_sqrt(y2)

        # Step 18-19: Adjust sign of y
        e3 = (self.curve.sgn0(y) == 1)
        y = self.curve.CMOV(y, -y % self.curve.PRIME_FIELD, e2 ^ e3)  # Ensure correct sign

        # Step 20-21: Scale coordinates
        s = (x * K) % self.curve.PRIME_FIELD
        t = (y * K) % self.curve.PRIME_FIELD

        s_t=(s,t)

        # Step 22: Return final mapped point
        return Point(*s_t)

    def glv_mul(self, other: int) -> Self:
        n = self.curve.ORDER
        v1, v2 = self.curve.glv.find_short_vectors(n, self.curve.glv.lamda)
        k1, k2 = self.curve.glv.decompose_scalar(other % n, v1, v2, n)
        phsi = self.compute_endomorphism()
        kp = self.scalar_mul(k1) + phsi.scalar_mul(k2)
        return kp

    def compute_endomorphism(self) -> Self:
        return self.scalar_mul(self.curve.glv.lamda)

    def string_to_point(self, octet_string):
        if isinstance(octet_string, str):  # Convert hex string to bytes
            octet_string = bytes.fromhex(octet_string)

        # Extract y-coordinate (ignore MSB of the first byte)
        y = int.from_bytes(octet_string, 'little') & ((1 << 255) - 1)

        # Recover x-coordinate
        x = self._x_recover(y)

        # Check if extracted LSB of x matches the stored bit
        if x & 1 != self._get_bit(octet_string, 256 - 1):
            x = self.curve.PRIME_FIELD - x  # Flip x if the bit doesn't match

        point = [x, y]
        return point

