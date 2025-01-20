import random
from typing import Tuple

class BandersnatchCurve:
    """Class for operations on the Bandersnatch elliptic curve using Elligator 2 mapping."""

    # Bandersnatch curve parameters
    P = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001
    a = -5  # -0x05
    d = 0x6389c12633c267cbc66e3bf86be3b6d8cb66677177e54f92b369f2f5188d58e7
    n = 0x1cfb69d4ca675f520cce760202687600ff8f87007419047174fd06b52876e7e1
    G = 0x664197ccb667315e6064e4ee81ad8c3586d5dcba508b7d150f3e12da9e666c2a

    @staticmethod
    def mod_inverse(a: int, m: int) -> int:
        """Calculate modular multiplicative inverse"""

        def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
            if a == 0:
                return b, 0, 1
            gcd, x1, y1 = extended_gcd(b % a, a)
            x = y1 - (b // a) * x1
            y = x1
            return gcd, x, y

        gcd, x, _ = extended_gcd(a, m)
        if gcd != 1:
            raise ValueError("Modular inverse does not exist")
        return (x % m + m) % m

    @staticmethod
    def is_square(x: int, p: int) -> bool:
        """Check if x is a quadratic residue modulo p."""
        if x == 0:
            return True
        return pow(x, (p - 1) // 2, p) == 1

    @staticmethod
    def mod_sqrt(a: int, p: int) -> int:
        """Calculate modular square root using Tonelli-Shanks algorithm"""
        if a == 0:
            return 0
        if not BandersnatchCurve.is_square(a, p):
            raise ValueError("No square root exists")

        q = p - 1
        s = 0
        while q % 2 == 0:
            q //= 2
            s += 1

        if s == 1:
            return pow(a, (p + 1) // 4, p)

        z = 2
        while BandersnatchCurve.is_square(z, p):
            z += 1

        m = s
        c = pow(z, q, p)
        t = pow(a, q, p)
        r = pow(a, (q + 1) // 2, p)

        while t != 1:
            i = 0
            temp = t
            while temp != 1:
                temp = (temp * temp) % p
                i += 1
                if i == m:
                    return 0

            b = pow(c, 1 << (m - i - 1), p)
            m = i
            c = (b * b) % p
            t = (t * c) % p
            r = (r * b) % p

        return r

    @staticmethod
    def find_z_ell2(p: int) -> int:
        """Find non-square Z value for Elligator 2"""
        ctr = 0x664197ccb667315e6064e4ee81ad8c3586d5dcba508b7d150f3e12da9e666c2a  # generator value
        while True:
            for z_cand in (ctr % p, -ctr % p):
                if not BandersnatchCurve.is_square(z_cand, p):
                    return z_cand
            ctr += 1

    @staticmethod
    def calculate_montgomery_params(a: int, d: int, p: int) -> Tuple[int, int]:
        """Calculate Montgomery curve parameters J and K"""
        # J = 2(a + d)/(a - d)
        # K = 4/(a - d)
        denom = (a - d) % p
        denom_inv = BandersnatchCurve.mod_inverse(denom, p)

        J = (2 * (a + d) * denom_inv) % p
        K = (4 * denom_inv) % p

        return J, K
    @staticmethod
    def elligator2_map(u: int, J: int, K: int, Z: int, p: int) -> Tuple[int, int]:
        """Implement Elligator 2 mapping"""
        # 1. Handle exceptional case
        if (1 + Z * pow(u, 2, p)) % p == 0:
            x1 = (-J * BandersnatchCurve.mod_inverse(K, p)) % p
        else:
            x1 = (-J * BandersnatchCurve.mod_inverse(K, p) * BandersnatchCurve.mod_inverse(1 + Z * pow(u, 2, p), p)) % p

        # 2. Handle x1 == 0 case
        if x1 == 0:
            x1 = (-J * BandersnatchCurve.mod_inverse(K, p)) % p

        # 3. Calculate gx1
        gx1 = (pow(x1, 3, p) + (J * pow(x1, 2, p) * BandersnatchCurve.mod_inverse(K, p)) +
               (x1 * BandersnatchCurve.mod_inverse(K * K, p))) % p

        # 4. Calculate x2
        x2 = (-x1 - J * BandersnatchCurve.mod_inverse(K, p)) % p

        # 5. Calculate gx2
        gx2 = (pow(x2, 3, p) + (J * pow(x2, 2, p) * BandersnatchCurve.mod_inverse(K, p)) +
               (x2 * BandersnatchCurve.mod_inverse(K * K, p))) % p

        # 6-7. Choose point based on square test
        if BandersnatchCurve.is_square(gx1, p):
            x = x1
            y = BandersnatchCurve.mod_sqrt(gx1, p)
            if y * 2 > p:  # sgn0(y) == 1
                y = (-y) % p
        else:
            x = x2
            y = BandersnatchCurve.mod_sqrt(gx2, p)
            if y * 2 < p:  # sgn0(y) == 0
                y = (-y) % p

        # 8-9. Scale point
        s = (x * K) % p
        t = (y * K) % p

        return s, t

    @staticmethod
    def montgomery_to_edwards(s: int, t: int, p: int) -> Tuple[int, int]:
        """
        Map Montgomery curve point to twisted Edwards curve following RFC9380 APPENDIX D1
        straight-line implementation.

        Input: (s, t), a point on the curve K * t^2 = s^3 + J * s^2 + s
        Output: (v, w), a point on an equivalent twisted Edwards curve
        """
        # 1. tv1 = s + 1
        tv1 = (s + 1) % p

        # 2. tv2 = tv1 * t        # (s + 1) * t
        tv2 = (tv1 * t) % p

        # 3. tv2 = inv0(tv2)      # 1 / ((s + 1) * t)
        try:
            tv2 = BandersnatchCurve.mod_inverse(tv2, p)
        except ValueError:
            tv2 = 0  # Handle the exceptional case where inverse doesn't exist

        # 4. v = tv2 * tv1        # 1 / t
        v = (tv2 * tv1) % p

        # 5. v = v * s            # s / t
        v = (v * s) % p

        # 6. w = tv2 * t          # 1 / (s + 1)
        w = (tv2 * t) % p

        # 7. tv1 = s - 1
        tv1 = (s - 1) % p

        # 8. w = w * tv1          # (s - 1) / (s + 1)
        w = (w * tv1) % p

        # 9. e = tv2 == 0
        e = tv2 == 0

        # 10. w = CMOV(w, 1, e)   # handle exceptional case
        w = 1 if e else w

        # 11. return (v, w)
        return v, w

    @staticmethod
    def check_is_point(v: int, w: int) -> bool:
        """Check if a point lies on the twisted Edwards curve."""
        lhs = (BandersnatchCurve.a * pow(v, 2, BandersnatchCurve.P) + pow(w, 2, BandersnatchCurve.P)) % BandersnatchCurve.P
        rhs = (1 + BandersnatchCurve.d * pow(v, 2, BandersnatchCurve.P) * pow(w, 2, BandersnatchCurve.P)) % BandersnatchCurve.P
        return lhs == rhs

    @staticmethod
    def generate_curve_point(u: int) -> Tuple[int, int]:
        """Generate a point on the Bandersnatch curve using Elligator 2."""
        J, K = BandersnatchCurve.calculate_montgomery_params(BandersnatchCurve.a, BandersnatchCurve.d, BandersnatchCurve.P)
        Z = BandersnatchCurve.find_z_ell2(BandersnatchCurve.P)
        s, t = BandersnatchCurve.elligator2_map(u, J, K, Z, BandersnatchCurve.P)
        return BandersnatchCurve.montgomery_to_edwards(s, t, BandersnatchCurve.P)
    @staticmethod
    def generate_random_point(u: int) -> Tuple[int, int]:
        """Generate a random point on the Bandersnatch curve"""
        try:
            v, w = BandersnatchCurve.generate_curve_point(u)
            if BandersnatchCurve.check_is_point(v, w):
                return v, w
        except ValueError:
            raise ValueError

# Example usage
def main():
    u = random.randint(0, BandersnatchCurve.P - 1)
    v, w = BandersnatchCurve.generate_random_point(u)

    print(f"Generated point on Bandersnatch curve:\nv = {hex(v)}\nw = {hex(w)}")

if __name__ == "__main__":
    main()
