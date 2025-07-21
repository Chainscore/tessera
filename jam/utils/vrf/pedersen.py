# from typing import Any
# from jam.types import ByteArray32, Boolean, ByteArray128


# def PedersenVRF(IETFVRF):
#     BLINDING_BASE = 123

#     def prove(self, message: ByteArray32) -> (ByteArray128, ByteArray128):
#         pass

#     def verify(self, proof: Any) -> Boolean:
#         pass

import math
import os
import hashlib
import random
from typing import Tuple, List, Dict

# Bandersnatch curve parameters
p = 0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001
a = -5
d = 0x6389C12633C267CBC66E3BF86BE3B6D8CB66677177E54F92B369F2F5188D58E7
n = 0x1CFB69D4CA675F520CCE760202687600FF8F87007419047174FD06B52876E7E1
G = (
    0x664197CCB667315E6064E4EE81AD8C3586D5DCBA508B7D150F3E12DA9E666C2A,
    0x43DE8D34436910F0AC41FC8837FC5CFF2595FD6107E443EA0485AD13E23B0E31,
)
# pedersen Blinding Base prameters
Bx = 14576224270591906826192118712803723445031237947873156025406837473427562701854
By = 14576224270591906826192118712803723445031237947873156025406837473427562701854
B = (Bx, By)
B_compressed = 0xAA5F60F3B3126FA406972D2023EE03BF281022209D13882199113619D57FFA54


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
    x1 = (
        (-J * mod_inverse(K, p) * mod_inverse(denom, p)) % p
        if denom
        else (-J * mod_inverse(K, p)) % p
    )

    gx1 = (
        pow(x1, 3, p)
        + J * pow(x1, 2, p) * mod_inverse(K, p)
        + x1 * mod_inverse(K * K, p)
    ) % p
    x2 = (-x1 - J * mod_inverse(K, p)) % p
    gx2 = (
        pow(x2, 3, p)
        + J * pow(x2, 2, p) * mod_inverse(K, p)
        + x2 * mod_inverse(K * K, p)
    ) % p

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
    denom_x = (a * x1**2 + y1**2) % p
    denom_y = (2 - a * x1**2 - y1**2) % p

    if denom_x == 0 or denom_y == 0:
        return (0, 1)  # Return identity if denominator is zero

    x3 = (2 * x1 * y1 * mod_inverse(denom_x, p)) % p
    y3 = ((y1**2 - a * x1**2) * mod_inverse(denom_y, p)) % p

    return (x3, y3)


def point_add(P1: Tuple[int, int], P2: Tuple[int, int]) -> Tuple[int, int]:
    """Add two points on the Bandersnatch curve"""
    x1, y1 = P1
    x2, y2 = P2
    if P1 == P2:
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


# modifed the Nonce Generation


def generate_nonce(secret_key: int, input_point: Tuple[int, int]) -> int:
    """Generate a nonce"""
    hashed_sk = hashlib.sha512(secret_key.to_bytes(32, "big")).digest()
    h_input = point_to_string(input_point)
    k_string = sha512(hashed_sk[32:] + h_input)
    return string_to_int(k_string) % n


# changed the Challenge Function
def challenge(
    Y: Tuple[int, int],
    I: Tuple[int, int],
    O: Tuple[int, int],
    R: Tuple[int, int],
    Ok: Tuple[int, int],
    ad: str,
) -> int:
    """Generate a challenge value"""
    data = (
        point_to_string(Y)
        + point_to_string(I)
        + point_to_string(O)
        + point_to_string(R)
        + point_to_string(Ok)
        + ad.encode()
    )
    return string_to_int(sha512(data))


# avoided using public key in generating ticket/proof and also modified the Function


def generate_ticket(
    secret_key: int, blinding_factor: int, input_point: Tuple[int, int], ad: str
) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Generate a VRF ticket"""
    O = point_mul(secret_key, input_point)
    k = generate_nonce(secret_key, input_point)
    Kb = generate_nonce(blinding_factor, input_point)
    Y = point_add(point_mul(secret_key, G), point_mul(blinding_factor, B))
    R = point_add(point_mul(k, G), point_mul(Kb, B))
    Ok = point_mul(k, input_point)
    # U, V = point_mul(k, G), point_mul(k, input_point)
    c = challenge(Y, input_point, O, R, Ok, ad)  # int
    s = (k + c * secret_key) % n  # int
    Sb = (Kb + c * blinding_factor) % n  # int
    return O, (Y, R, Ok, s, Sb)


def point_neg(point: Tuple[int, int]) -> Tuple[int, int]:
    """Negate a point on the curve."""
    x, y = point
    return (-x % p, y)


def point_subtract(p1: Tuple[int, int], p2: Tuple[int, int]) -> Tuple[int, int]:
    """Subtract two points."""
    return point_add(p1, point_neg(p2))


# Changed the Verify ticket Functionality
def verify_ticket(
    input_point: Tuple[int, int],
    additional_data: str,
    output_point: Tuple[int, int],
    proof,
) -> bool:
    """Verify a VRF ticket"""
    Y, R, Ok, s, Sb = proof
    # s int
    # sb int
    # rest are points

    # U = point_subtract(point_mul(s, G), point_mul(c, public_key))
    # V = point_subtract(point_mul(s, input_point), point_mul(c, output_point))
    c = challenge(Y, input_point, output_point, R, Ok, additional_data)  # int
    Theta0 = point_add(Ok, point_mul(c, output_point)) == point_mul(s, input_point)
    Theta1 = point_add(R, point_mul(c, Y)) == point_add(
        point_mul(s, G), point_mul(Sb, G)
    )
    return Theta0 == Theta1


def generate_random_point(u: int) -> Tuple[int, int]:
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
    hash_value = int.from_bytes(hashlib.sha256(message.encode()).digest(), "big")

    # Find a valid point on the curve
    x = hash_value % p
    return x


def point_to_string(P: Tuple[int, int]) -> bytes:
    """Convert a point to bytes"""
    x, y = P
    return x.to_bytes(32, "big") + y.to_bytes(32, "big")


def string_to_int(s: bytes) -> int:
    """Convert bytes to an integer"""
    return int.from_bytes(s, "big")


def sha512(data: bytes) -> bytes:
    """Calculate SHA-512 hash"""
    return hashlib.sha512(data).digest()


def select_winning_ticket(tickets: List[Dict]) -> Tuple[List[Dict], Dict]:
    """Select the winning ticket from valid ticket.py based on minimum output_point"""
    valid_tickets = [ticket for ticket in tickets if ticket["valid"]]
    if not valid_tickets:
        return [], None

    winning_ticket = min(valid_tickets, key=lambda ticket: ticket["output_point"])
    return valid_tickets, winning_ticket


def main():
    """Main function to generate and verify VRF ticket.py"""
    tickets = []
    validators = ["Hello", "Hello Computer", "Hello Coder"]
    b = 0xAA5F60F3B3126FA406972D2023EE03BF281022209D13882199113619D57FFA54

    for i in range(len(validators)):
        secret_key = random.randint(1, p - 1)
        # input_point=generate_random_point()
        input_point = generate_random_point(hash_to_point(validators[i]))
        # print(input_point)
        ad = f"Ticket {i + 1}"

        output_point, proof = generate_ticket(secret_key, b, input_point, ad)
        # print(proof)
        public_key = point_mul(secret_key, G)
        valid = verify_ticket(input_point, ad, output_point, proof)

        tickets.append({"proof": proof, "valid": valid, "output_point": output_point})
        print(f"Ticket {i + 1}: {'VALID' if valid else 'INVALID'}")

    valid_tickets, winning_ticket = select_winning_ticket(tickets)

    if valid_tickets:
        print("\nValid ticket.py:")
        for idx, ticket in enumerate(valid_tickets, 1):
            print(
                f"Ticket {idx}: Proof {ticket['proof']}, Output Point: {ticket['output_point']}"
            )

        print(
            f"\nWinning ticket: Proof {winning_ticket['proof']}, Output Point: {winning_ticket['output_point']}"
        )
    else:
        print("\nNo valid ticket.py found.")


if __name__ == "__main__":
    main()
