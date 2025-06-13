import hashlib
import random
from typing import Tuple, List, Dict
from bandersnatch_el2_cls import BandersnatchCurve

class PedersenVRF:
    """Pedersen-based Verifiable Random Function (VRF) implementation."""

    # Bandersnatch curve parameters
    p = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001
    a = -5
    d = 0x6389c12633c267cbc66e3bf86be3b6d8cb66677177e54f92b369f2f5188d58e7
    n = 0x1cfb69d4ca675f520cce760202687600ff8f87007419047174fd06b52876e7e1
    G = (
        0x664197ccb667315e6064e4ee81ad8c3586d5dcba508b7d150f3e12da9e666c2a,
        0x43de8d34436910f0ac41fc8837fc5cff2595fd6107e443ea0485ad13e23b0e31
    )
    # Pedersen Blinding Base parameters
    Bx = 14576224270591906826192118712803723445031237947873156025406837473427562701854
    By = Bx
    B = (Bx, By)
    B_compressed = 0xaa5f60f3b3126fa406972d2023ee03bf281022209d13882199113619d57ffa54

    @staticmethod
    def mod_inverse(a: int, m: int) -> int:
        """Calculate modular multiplicative inverse."""
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
    def sha512(data: bytes) -> bytes:
        """Calculate SHA-512 hash."""
        return hashlib.sha512(data).digest()

    @staticmethod
    def point_to_string(P: Tuple[int, int]) -> bytes:
        """Convert a point to bytes."""
        x, y = P
        return x.to_bytes(32, 'little') + y.to_bytes(32, 'little')

    @staticmethod
    def string_to_int(s: bytes) -> int:
        """Convert bytes to an integer."""
        return int.from_bytes(s, 'little')
    @staticmethod
    def hash_to_point(message:str)->int:
        """
        Map a message deterministically to a point on the SECP256k1 curve.
        """
        # Hash the message to produce an integer
        hash_value = int.from_bytes(hashlib.sha256(message.encode()).digest(), 'little')

        # Find a valid point on the curve
        x = hash_value % PedersenVRF.p
        return x
    @staticmethod
    def point_add(P1: Tuple[int, int], P2: Tuple[int, int]) -> Tuple[int, int]:
        """Add two points on the Bandersnatch curve."""
        x1, y1 = P1
        x2, y2 = P2
        if P1 == P2:
            return PedersenVRF.point_double(P1)

        if P1 == (0, 1):
            return P2
        if P2 == (0, 1):
            return P1

        x1y2 = (x1 * y2) % PedersenVRF.p
        y1x2 = (y1 * x2) % PedersenVRF.p
        dx1x2y1y2 = (PedersenVRF.d * x1 * x2 * y1 * y2) % PedersenVRF.p

        try:
            x3 = ((x1y2 + y1x2) * PedersenVRF.mod_inverse(1 + dx1x2y1y2, PedersenVRF.p)) % PedersenVRF.p
            y3 = ((y1 * y2 - PedersenVRF.a * x1 * x2) * PedersenVRF.mod_inverse(1 - dx1x2y1y2, PedersenVRF.p)) % PedersenVRF.p
        except ValueError:
            return (0, 1)

        return x3, y3

    @staticmethod
    def point_double(P: Tuple[int, int]) -> Tuple[int, int]:
        """Point doubling on the twisted Edwards curve."""
        x1, y1 = P
        if y1 == 0:
            return (0, 1)

        denom_x = (PedersenVRF.a * x1 ** 2 + y1 ** 2) % PedersenVRF.p
        denom_y = (2 - PedersenVRF.a * x1 ** 2 - y1 ** 2) % PedersenVRF.p

        if denom_x == 0 or denom_y == 0:
            return (0, 1)

        x3 = (2 * x1 * y1 * PedersenVRF.mod_inverse(denom_x, PedersenVRF.p)) % PedersenVRF.p
        y3 = ((y1 ** 2 - PedersenVRF.a * x1 ** 2) * PedersenVRF.mod_inverse(denom_y, PedersenVRF.p)) % PedersenVRF.p

        return (x3, y3)

    @staticmethod
    def point_mul(k: int, P: Tuple[int, int]) -> Tuple[int, int]:
        """Multiply a point by a scalar."""
        result = (0, 1)
        addend = P

        while k:
            if k & 1:
                result = PedersenVRF.point_add(result, addend)
            addend = PedersenVRF.point_double(addend)
            k >>= 1

        return result

    @staticmethod
    def challenge(Y, I, O, R, Ok, ad) -> int:
        """Generate a challenge value."""
        data = PedersenVRF.point_to_string(Y) + PedersenVRF.point_to_string(I) + \
               PedersenVRF.point_to_string(O) + PedersenVRF.point_to_string(R) + \
               PedersenVRF.point_to_string(Ok) + ad.encode()
        return PedersenVRF.string_to_int(PedersenVRF.sha512(data))

    @staticmethod
    def generate_ticket(secret_key: int, blinding_factor: int, input_point: Tuple[int, int], ad: str):
        """Generate a VRF ticket."""
        O = PedersenVRF.point_mul(secret_key, input_point)
        k = random.randint(1, PedersenVRF.n - 1)
        Kb = random.randint(1, PedersenVRF.n - 1)
        Y = PedersenVRF.point_add(PedersenVRF.point_mul(secret_key, PedersenVRF.G), PedersenVRF.point_mul(blinding_factor, PedersenVRF.B))
        R = PedersenVRF.point_add(PedersenVRF.point_mul(k, PedersenVRF.G), PedersenVRF.point_mul(Kb, PedersenVRF.B))
        Ok = PedersenVRF.point_mul(k, input_point)
        c = PedersenVRF.challenge(Y, input_point, O, R, Ok, ad)
        s = (k + c * secret_key) % PedersenVRF.n
        Sb = (Kb + c * blinding_factor) % PedersenVRF.n

        return O, (Y, R, Ok, s, Sb)

    @staticmethod
    def verify_ticket(input_point, ad, output_point, proof):
        """Verify a VRF ticket."""
        Y, R, Ok, s, Sb = proof
        c = PedersenVRF.challenge(Y, input_point, output_point, R, Ok, ad)
        Theta0 = PedersenVRF.point_add(Ok, PedersenVRF.point_mul(c, output_point)) == PedersenVRF.point_mul(s, input_point)
        Theta1 = PedersenVRF.point_add(R, PedersenVRF.point_mul(c, Y)) == PedersenVRF.point_add(PedersenVRF.point_mul(s, PedersenVRF.G), PedersenVRF.point_mul(Sb, PedersenVRF.G))
        return Theta0 == Theta1

    def select_winning_ticket(tickets: List[Dict]) -> Tuple[List[Dict], Dict]:
        """Select the winning ticket from valid ticket.py based on the minimum output_point."""
        valid_tickets = [ticket for ticket in tickets if ticket['valid']]
        if not valid_tickets:
            return [], None

        winning_ticket = min(valid_tickets, key=lambda ticket: ticket['output_point'])
        return valid_tickets, winning_ticket




def main():
    """Main function to generate and verify VRF ticket.py"""
    tickets = []
    validators = ["Hello", "Hello Computer", "Hello Coder"]
    b = 0xaa5f60f3b3126fa406972d2023ee03bf281022209d13882199113619d57ffa54

    for i in range(len(validators)):
        secret_key = random.randint(1, PedersenVRF.p - 1)
        input_point = BandersnatchCurve.generate_random_point(PedersenVRF.hash_to_point(validators[i]))
        ad = f"Ticket {i + 1}"

        output_point, proof = PedersenVRF.generate_ticket(secret_key, b, input_point, ad)
        valid = PedersenVRF.verify_ticket(input_point, ad, output_point, proof)

        tickets.append({
            'proof': proof,
            'valid': valid,
            'output_point': output_point
        })

        print(f"{input_point}")
        print(f"Ticket {i + 1}: {'VALID' if valid else 'INVALID'}")

    # Call select_winning_ticket correctly using the class
    valid_tickets, winning_ticket = PedersenVRF.select_winning_ticket(tickets)

    if valid_tickets:
        print("\nValid ticket.py:")
        for idx, ticket in enumerate(valid_tickets, 1):
            print(f"Ticket {idx}: Proof {ticket['proof']}, Output Point: {ticket['output_point']}")

        print(f"\nWinning ticket: Proof {winning_ticket['proof']}, Output Point: {winning_ticket['output_point']}")
    else:
        print("\nNo valid ticket.py found.")

if __name__ == "__main__":
    main()
