from typing import Tuple
import math

# Bandersnatch curve parameters
P = 0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
a = -5  # -0x05
d = 0x6389C12633C267CBC66E3BF86BE3B6D8CB66677177E54F92B369F2F5188D58E7
# d=math.ceil(138827208126141220649022263972958607803/171449701953573178309673572579671231137)
n = 0x1CFB69D4CA675F520CCE760202687600FF8F87007419047174FD06B52876E7E1
G = 0x664197CCB667315E6064E4EE81AD8C3586D5DCBA508B7D150F3E12DA9E666C2A


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


def is_square(x: int, p: int) -> bool:
    """Check if x is a quadratic residue modulo p"""
    if x == 0:
        return True
    return pow(x, (p - 1) // 2, p) == 1


def mod_sqrt(a: int, p: int) -> int:
    """Calculate modular square root using Tonelli-Shanks algorithm"""
    if a == 0:
        return 0
    if not is_square(a, p):
        raise ValueError("No square root exists")

    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1

    if s == 1:
        return pow(a, (p + 1) // 4, p)

    z = 2
    while is_square(z, p):
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


def find_z_ell2(p: int) -> int:
    """Find non-square Z value for Elligator 2"""
    ctr = 0x664197CCB667315E6064E4EE81AD8C3586D5DCBA508B7D150F3E12DA9E666C2A  # generator value
    while True:
        for z_cand in (ctr % p, -ctr % p):
            if not is_square(z_cand, p):
                return z_cand
        ctr += 1


def calculate_montgomery_params(a: int, d: int, p: int) -> Tuple[int, int]:
    """Calculate Montgomery curve parameters J and K"""
    # J = 2(a + d)/(a - d)
    # K = 4/(a - d)
    denom = (a - d) % p
    denom_inv = mod_inverse(denom, p)

    J = (2 * (a + d) * denom_inv) % p
    K = (4 * denom_inv) % p

    return J, K


def elligator2_map(u: int, J: int, K: int, Z: int, p: int) -> Tuple[int, int]:
    """Implement Elligator 2 mapping"""
    # 1. Handle exceptional case
    if (1 + Z * pow(u, 2, p)) % p == 0:
        x1 = (-J * mod_inverse(K, p)) % p
    else:
        x1 = (-J * mod_inverse(K, p) * mod_inverse(1 + Z * pow(u, 2, p), p)) % p

    # 2. Handle x1 == 0 case
    if x1 == 0:
        x1 = (-J * mod_inverse(K, p)) % p

    # 3. Calculate gx1
    gx1 = (
        pow(x1, 3, p)
        + (J * pow(x1, 2, p) * mod_inverse(K, p))
        + (x1 * mod_inverse(K * K, p))
    ) % p

    # 4. Calculate x2
    x2 = (-x1 - J * mod_inverse(K, p)) % p

    # 5. Calculate gx2
    gx2 = (
        pow(x2, 3, p)
        + (J * pow(x2, 2, p) * mod_inverse(K, p))
        + (x2 * mod_inverse(K * K, p))
    ) % p

    # 6-7. Choose point based on square test
    if is_square(gx1, p):
        x = x1
        y = mod_sqrt(gx1, p)
        if y * 2 > p:  # sgn0(y) == 1
            y = (-y) % p
    else:
        x = x2
        y = mod_sqrt(gx2, p)
        if y * 2 < p:  # sgn0(y) == 0
            y = (-y) % p

    # 8-9. Scale point
    s = (x * K) % p
    t = (y * K) % p

    return s, t


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
        tv2 = mod_inverse(tv2, p)
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


def check_is_point(v, w):
    left = (a * pow(v, 2, P) + pow(w, 2, P)) % P
    right = (1 + d * pow(v, 2, P) * pow(w, 2, P)) % P
    return left == right


def generate_curve_point(u: int) -> Tuple[int, int]:
    """Generate a point on the Bandersnatch curve using Elligator 2"""
    # Calculate Montgomery parameters
    J, K = calculate_montgomery_params(a, d, P)

    # Find Z value
    Z = find_z_ell2(P)

    # Map to Montgomery curve
    s, t = elligator2_map(u, J, K, Z, P)

    # Map to Edwards curve
    v, w = montgomery_to_edwards(s, t, P)

    return v, w


import random


# Example usage
def main():
    # Generate a point using a random value
    u = random.randint(0, P - 1)  # Example input

    v, w = generate_curve_point(u)
    valid = check_is_point(v, w)

    print(f"Generated point on Bandersnatch curve:")
    print(f"v = {hex(v)}")
    print(f"w = {hex(w)}")
    if valid:
        print("Point Lies On Curve")
    else:
        print("Point is not On the Curve")


if __name__ == "__main__":
    main()


# def str_to_crv_ell2(input: str):
#     pass
