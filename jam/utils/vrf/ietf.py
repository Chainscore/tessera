# from typing import Any
# from jam.types.base.boolean import Boolean
# from jam.types.base.byte_array import ByteArray32, ByteArray128
# from jam.utils.vrf.base import VRF
# from .utils import str_to_crv_ell2

# class IETFVRF(VRF):
#     GENERATOR_X = 123
#     GENERATOR_Y = 321

#     def prove(self, message: ByteArray32) -> (ByteArray128, ByteArray128):
#         # TODO: Implement IETF VRF
#         str_to_crv_ell2()
#         pass
    
#     def verify(self, proof: Any) -> Boolean:
#         # TODO: Implement IETF VRF
#         pass
import math
import os
import hashlib
import random
from typing import Tuple, List, Dict

# Bandersnatch curve parameters
p = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001
a = -5
d = 0x6389c12633c267cbc66e3bf86be3b6d8cb66677177e54f92b369f2f5188d58e7
n = 0x1cfb69d4ca675f520cce760202687600ff8f87007419047174fd06b52876e7e1
G = (
    0x664197ccb667315e6064e4ee81ad8c3586d5dcba508b7d150f3e12da9e666c2a,
    0x43de8d34436910f0ac41fc8837fc5cff2595fd6107e443ea0485ad13e23b0e31
)


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
    return pow(x, (p - 1) // 2, p) == 1 if x != 0 else True


def mod_sqrt(a: int, p: int) -> int:
    """Calculate modular square root using Tonelli-Shanks algorithm"""
    if a == 0:
        return 0
    if not is_square(a, p):
        raise ValueError("No square root exists")

    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1

    if s == 1:
        return pow(a, (p + 1) // 4, p)

    z = 2
    while is_square(z, p):
        z += 1

    m, c, t, r = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) // 2, p)
    while t != 1:
        i, temp = 0, t
        while temp != 1:
            temp = (temp * temp) % p
            i += 1

        b = pow(c, 1 << (m - i - 1), p)
        m = i
        c = (b * b) % p
        t = (t * c) % p
        r = (r * b) % p

    return r


def calculate_montgomery_params(a: int, d: int, p: int) -> Tuple[int, int]:
    """Calculate Montgomery curve parameters J and K"""
    denom = (a - d) % p
    denom_inv = mod_inverse(denom, p)
    J = (2 * (a + d) * denom_inv) % p
    K = (4 * denom_inv) % p
    return J, K


def find_z_ell2(p: int) -> int:
    """Find a non-square Z value for Elligator 2"""
    ctr = random.randint(1, p - 1)
    while True:
        for z_cand in (ctr % p, -ctr % p):
            if not is_square(z_cand, p):
                return z_cand
        ctr += 1


def elligator2_map(u: int, J: int, K: int, Z: int, p: int) -> Tuple[int, int]:
    """Implement Elligator 2 mapping"""
    denom = (1 + Z * pow(u, 2, p)) % p
    x1 = (-J * mod_inverse(K, p) * mod_inverse(denom, p)) % p if denom else (-J * mod_inverse(K, p)) % p

    gx1 = (pow(x1, 3, p) + J * pow(x1, 2, p) * mod_inverse(K, p) + x1 * mod_inverse(K * K, p)) % p
    x2 = (-x1 - J * mod_inverse(K, p)) % p
    gx2 = (pow(x2, 3, p) + J * pow(x2, 2, p) * mod_inverse(K, p) + x2 * mod_inverse(K * K, p)) % p

    if is_square(gx1, p):
        x, y = x1, mod_sqrt(gx1, p)
    else:
        x, y = x2, mod_sqrt(gx2, p)

    if y * 2 > p:
        y = (-y) % p

    s = (x * K) % p
    t = (y * K) % p
    return s, t


def montgomery_to_edwards(s: int, t: int, p: int) -> Tuple[int, int]:
    """Map Montgomery curve point to twisted Edwards curve"""
    tv1 = (s + 1) % p
    tv2 = (tv1 * t) % p
    try:
        tv2 = mod_inverse(tv2, p)
    except ValueError:
        tv2 = 0

    v = (tv2 * tv1 * s) % p
    w = (tv2 * t * (s - 1)) % p
    return v, 1 if tv2 == 0 else w


def generate_curve_point(u: int) -> Tuple[int, int]:
    """Generate a point on the Bandersnatch curve using Elligator 2"""
    J, K = calculate_montgomery_params(a, d, p)
    Z = find_z_ell2(p)
    s, t = elligator2_map(u, J, K, Z, p)
    return montgomery_to_edwards(s, t, p)


def check_is_point(P: Tuple[int, int]) -> bool:
    """Check if a point lies on the twisted Edwards curve"""
    v, w = P
    lhs = (a * pow(v, 2, p) + pow(w, 2, p)) % p
    rhs = (1 + d * pow(v, 2, p) * pow(w, 2, p)) % p
    return lhs == rhs

# def point_double(P):
#     """Point doubling on the twisted Edwards curve."""
#     x1, y1 = P
#
#     # Check if the point is at infinity (identity element)
#     if y1 == 0:
#         return (0, 1)  # Return the identity point in twisted Edwards form
#
#     # Lambda (slope of the tangent line)
#     lam = (3 * x1 ** 2 + a) * mod_inverse(2 * y1, p) % p
#
#     # Calculate the x and y coordinates of the doubled point
#     x3 = (lam ** 2 - 2 * x1) % p
#     y3 = (lam * (x1 - x3) - y1) % p
#
#     return (x3, y3)

def point_double(P: Tuple[int, int]) -> Tuple[int, int]:
    """Point doubling on the twisted Edwards curve."""
    x1, y1 = P

    # Check if the point is at infinity (identity element)
    if y1 == 0:
        return (0, 1)  # Return the identity point in twisted Edwards form

    # Calculate new coordinates using the doubling formula
    denom_x = (a * x1 ** 2 + y1 ** 2) % p
    denom_y = (2 - a * x1 ** 2 - y1 ** 2) % p

    if denom_x == 0 or denom_y == 0:
        return (0, 1)  # Return identity if denominator is zero

    x3 = (2 * x1 * y1 * mod_inverse(denom_x, p)) % p
    y3 = ((y1 ** 2 - a * x1 ** 2) * mod_inverse(denom_y, p)) % p

    return (x3, y3)

def point_add(P1: Tuple[int, int], P2: Tuple[int, int]) -> Tuple[int, int]:
    """Add two points on the Bandersnatch curve"""
    x1, y1 = P1
    x2, y2 = P2
    if P1==P2:
        return point_double(P1)

    if P1 == (0, 1):
        return P2
    if P2 == (0, 1):
        return P1

    x1y2 = (x1 * y2) % p
    y1x2 = (y1 * x2) % p
    y1y2 = (y1 * y2) % p
    x1x2 = (x1 * x2) % p
    dx1x2y1y2 = (d * x1x2 * y1y2) % p

    try:
        x3 = ((x1y2 + y1x2) * mod_inverse(1 + dx1x2y1y2, p)) % p
        y3 = ((y1y2 - a * x1x2) * mod_inverse(1 - dx1x2y1y2, p)) % p
    except ValueError:
        # print(f"Failed to compute modular inverse in point_add: P1={P1}, P2={P2}")
        return (0, 1)  # Return identity point in case of failure

    return x3, y3


def point_mul(k: int, P: Tuple[int, int]) -> Tuple[int, int]:
    """Multiply a point by a scalar"""
    result = (0, 1)
    addend = P

    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1

    return result


def generate_nonce(secret_key: int, input_point: Tuple[int, int]) -> int:
    """Generate a nonce"""
    hashed_sk = hashlib.sha512(secret_key.to_bytes(32, 'big')).digest()
    h_input = point_to_string(input_point)
    k_string = sha512(hashed_sk[32:] + h_input)
    return string_to_int(k_string) % n


def challenge(Y: Tuple[int, int], I: Tuple[int, int], O: Tuple[int, int],
              U: Tuple[int, int], V: Tuple[int, int], ad: str) -> int:
    """Generate a challenge value"""
    data = point_to_string(Y) + point_to_string(I) + point_to_string(O) + \
           point_to_string(U) + point_to_string(V) + ad.encode()
    return string_to_int(sha512(data))


def generate_ticket(secret_key: int, input_point: Tuple[int, int], ad: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Generate a VRF ticket"""
    O = point_mul(secret_key, input_point)
    Y = point_mul(secret_key, G)
    k = generate_nonce(secret_key, input_point)
    U, V = point_mul(k, G), point_mul(k, input_point)
    c = challenge(Y, input_point, O, U, V, ad)
    s = (k + c * secret_key) % n
    return O, (c, s)

def point_neg(point: Tuple[int, int]) -> Tuple[int, int]:
    """Negate a point on the curve."""
    x, y = point
    return (-x % p, y)


def point_subtract(p1: Tuple[int, int], p2: Tuple[int, int]) -> Tuple[int, int]:
    """Subtract two points."""
    return point_add(p1, point_neg(p2))





def verify_ticket(public_key: Tuple[int, int], input_point: Tuple[int, int],
                  additional_data: str, output_point: Tuple[int, int],
                  proof: Tuple[int, int]) -> bool:
    """Verify a VRF ticket"""
    c, s = proof
    U = point_subtract(point_mul(s, G), point_mul(c, public_key))
    V = point_subtract(point_mul(s, input_point), point_mul(c, output_point))
    return c == challenge(public_key, input_point, output_point, U, V, additional_data)


def generate_random_point(u:int) -> Tuple[int, int]:
    """Generate a random point on the Bandersnatch curve"""
    while True:
        # u = random.randrange(p)
        try:
            v, w = generate_curve_point(u)
            if check_is_point((v, w)):
                return v, w
        except ValueError:
            raise ValueError

def hash_to_point(message):
    """
    Map a message deterministically to a point on the SECP256k1 curve.
    """
    # Hash the message to produce an integer
    hash_value = int.from_bytes(hashlib.sha256(message.encode()).digest(), 'big')

    # Find a valid point on the curve
    x = hash_value % p
    return x


def point_to_string(P: Tuple[int, int]) -> bytes:
    """Convert a point to bytes"""
    x, y = P
    return x.to_bytes(32, 'big') + y.to_bytes(32, 'big')


def string_to_int(s: bytes) -> int:
    """Convert bytes to an integer"""
    return int.from_bytes(s, 'big')


def sha512(data: bytes) -> bytes:
    """Calculate SHA-512 hash"""
    return hashlib.sha512(data).digest()


def select_winning_ticket(tickets: List[Dict]) -> Tuple[List[Dict], Dict]:
    """Select the winning ticket from valid ticket.py based on minimum output_point"""
    valid_tickets = [ticket for ticket in tickets if ticket['valid']]
    if not valid_tickets:
        return [], None

    winning_ticket = min(valid_tickets, key=lambda ticket: ticket['output_point'])
    return valid_tickets, winning_ticket


def main():
    """Main function to generate and verify VRF ticket.py"""
    tickets = []
    validators = ["Hello", "Hello Computer", "Hello Coder"]

    for i in range(len(validators)):
        secret_key = random.randint(1, p- 1)
        # input_point=generate_random_point()
        input_point = generate_random_point(hash_to_point(validators[i]))
        ad = f"Ticket {i + 1}"
        output_point, proof = generate_ticket(secret_key, input_point, ad)
        public_key = point_mul(secret_key, G)
        valid = verify_ticket(public_key, input_point, ad, output_point, proof)

        tickets.append({
            'proof': proof,
            'valid': valid,
            'output_point': output_point
        })
        print(f"Ticket {i + 1}: {'VALID' if valid else 'INVALID'}")

    valid_tickets, winning_ticket = select_winning_ticket(tickets)

    if valid_tickets:
        print("\nValid ticket.py:")
        for idx, ticket in enumerate(valid_tickets, 1):
            print(f"Ticket {idx}: Proof {ticket['proof']}, Output Point: {ticket['output_point']}")

        print(f"\nWinning ticket: Proof {winning_ticket['proof']}, Output Point: {winning_ticket['output_point']}")
    else:
        print("\nNo valid ticket.py found.")


if __name__=="__main__":
    main()
