from typing import Tuple

from sympy import mod_inverse
from jam.ring_vrf.ring_proof.constants import S_PRIME as S_PRIME_FIELD, PaddingPoint, Blinding_Base, S_B
from jam.ring_vrf.ring_proof.constants import S_A,SeedPoint,S_ORDER
from jam.ring_vrf.ring_proof.short_weierstrass import is_on_weierstrass, twisted_edward_to_sw


def point_addition(point1, point2):
    """
    input: point1 and point2
    output: Point addition
    """
    # If one of the points is the identity, return the other.
    if point1 is None:
        return point2
    if point2 is None:
        return point1
    # Otherwise, do the normal point addition (using the curve's parameters).
    x1, y1 = point1
    x2, y2 = point2
    if x1 == x2 and y1 == y2:
        return point_doubling(point1)
    lam = (y2 - y1) * mod_inverse(x2 - x1, S_PRIME_FIELD) % S_PRIME_FIELD
    x3 = (lam * lam - x1 - x2) % S_PRIME_FIELD
    y3 = (lam * (x1 - x3) - y1) % S_PRIME_FIELD
    return (x3, y3)


def point_multiplication(k, point):
    """
    input: point P, scalr k
    output: point multiplication.
    """
    result = None  # Identity (0,1,0: Projective)
    addend = point
    while k:
        if k & 1:
            result = point_addition(result, addend)
        addend = point_doubling(addend)
        k >>= 1
    return result


def point_doubling(point):
    """
    input: point
    output: doubled point
    """
    #need Short Weierstrass A,B constants(satisfied)
    x1,y1=point
    x1=int(x1)
    y1=int(y1)
    slope=(3* x1**2 % S_PRIME_FIELD + S_A  % S_PRIME_FIELD)* mod_inverse(2*y1,S_PRIME_FIELD) % S_PRIME_FIELD
    x3=(pow(slope,2, S_PRIME_FIELD) - 2*x1 % S_PRIME_FIELD) % S_PRIME_FIELD
    y3=(slope*(x1-x3) % S_PRIME_FIELD -y1) % S_PRIME_FIELD
    # print(y3>S_PRIME_FIELD)
    # print(x3>S_PRIME_FIELD)
    return x3,y3


def point_subtraction(point1, point2):
    """
    input: point1 and point2
    output: point1 - point2 on the short Weierstrass curve
    """
    if point2 is None:
        return point1
    # Negate the y-coordinate of point2
    x2, y2 = point2
    neg_point2 = (x2, (-y2) % S_PRIME_FIELD)
    return point_addition(point1, neg_point2)



def mod_sqrt(a, p):
    """Tonelli–Shanks algorithm for general primes p"""
    # Check if square root exists
    if pow(a, (p - 1) // 2, p) != 1:
        raise ValueError("No square root exists")

    # Simple case
    if p % 4 == 3:
        return pow(a, (p + 1) // 4, p)

    # Find Q and S such that p - 1 = Q * 2^S with Q odd
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1

    # Find a quadratic non-residue z
    z = 2
    while pow(z, (p - 1) // 2, p) != p - 1:
        z += 1

    m = s
    c = pow(z, q, p)
    t = pow(a, q, p)
    r = pow(a, (q + 1) // 2, p)

    while t != 1:
        i = 1
        temp = pow(t, 2, p)
        while temp != 1:
            temp = pow(temp, 2, p)
            i += 1
            if i == m:
                raise ValueError("No square root found")

        b = pow(c, 2 ** (m - i - 1), p)
        m = i
        c = pow(b, 2, p)
        t = (t * c) % p
        r = (r * b) % p

    return r

def compress_point(point:Tuple[int,int], p: int) -> bytes:
    x,y=point
    prefix = 0x02 if y % 2 == 0 else 0x03
    x_bytes = x.to_bytes((p.bit_length() + 7) // 8, 'big')
    return bytes([prefix]) + x_bytes

def decompress_point(compressed: bytes, a: int, b: int, p: int):
    prefix = compressed[0]
    x = int.from_bytes(compressed[1:], 'big')
    rhs = (pow(x, 3, p) + a * x + b) % p
    y = mod_sqrt(rhs, p)

    # Choose correct y based on prefix
    if (y % 2 == 0 and prefix == 0x02) or (y % 2 == 1 and prefix == 0x03):
        return (x, y)
    else:
        return (x, p - y)


def main():
    from jam.ring_vrf.ring_proof.constants import Blinding_Base,PaddingPoint, SeedPoint
    sw_bb=twisted_edward_to_sw(Blinding_Base)
    # sw_pp=twisted_edward_to_sw(PaddingPoint)
    # sw_sp=twisted_edward_to_sw(SeedPoint)
    print(sw_bb)
    print(compress_point(sw_bb, S_PRIME_FIELD))
    print(decompress_point(b'\x03\n\xf5W\x8d\xaa\xfc\xa8_\xf4\xfb\x0eR\xefy|\x8e\xe2\xdd\x87\\C\x03\x0bG\xd8\xd8"NU\x95\xca\xc2', S_A, S_B,S_PRIME_FIELD))

if __name__=='__main__':
    main()

