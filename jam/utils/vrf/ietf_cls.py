import math
import os
import hashlib
import random
from typing import Tuple, List, Dict
from dataclasses import dataclass
from bandersnatch_el2_cls import  BandersnatchCurve

@dataclass
class Ticket:
    proof: Tuple[int, int]
    valid: bool
    output_point: Tuple[int, int]


class IETF:
    def __init__(self):
        # Bandersnatch curve parameters
        self.p = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001
        self.a = -5
        self.d = 0x6389c12633c267cbc66e3bf86be3b6d8cb66677177e54f92b369f2f5188d58e7
        self.n = 0x1cfb69d4ca675f520cce760202687600ff8f87007419047174fd06b52876e7e1
        self.G = (
            0x664197ccb667315e6064e4ee81ad8c3586d5dcba508b7d150f3e12da9e666c2a,
            0x43de8d34436910f0ac41fc8837fc5cff2595fd6107e443ea0485ad13e23b0e31
        )

    def mod_inverse(self, a: int, m: int) -> int:
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

    def is_square(self, x: int, p: int) -> bool:
        """Check if x is a quadratic residue modulo p"""
        return pow(x, (p - 1) // 2, p) == 1 if x != 0 else True

    def mod_sqrt(self, a: int, p: int) -> int:
        """Calculate modular square root using Tonelli-Shanks algorithm"""
        if a == 0:
            return 0
        if not self.is_square(a, p):
            raise ValueError("No square root exists")

        q, s = p - 1, 0
        while q % 2 == 0:
            q //= 2
            s += 1

        if s == 1:
            return pow(a, (p + 1) // 4, p)

        z = 2
        while self.is_square(z, p):
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

    def point_double(self, P: Tuple[int, int]) -> Tuple[int, int]:
        """Point doubling on the twisted Edwards curve"""
        x1, y1 = P

        if y1 == 0:
            return (0, 1)

        denom_x = (self.a * x1 ** 2 + y1 ** 2) % self.p
        denom_y = (2 - self.a * x1 ** 2 - y1 ** 2) % self.p

        if denom_x == 0 or denom_y == 0:
            return (0, 1)

        x3 = (2 * x1 * y1 * self.mod_inverse(denom_x, self.p)) % self.p
        y3 = ((y1 ** 2 - self.a * x1 ** 2) * self.mod_inverse(denom_y, self.p)) % self.p

        return (x3, y3)

    def point_add(self, P1: Tuple[int, int], P2: Tuple[int, int]) -> Tuple[int, int]:
        """Add two points on the Bandersnatch curve"""
        x1, y1 = P1
        x2, y2 = P2

        if P1 == P2:
            return self.point_double(P1)

        if P1 == (0, 1):
            return P2
        if P2 == (0, 1):
            return P1

        x1y2 = (x1 * y2) % self.p
        y1x2 = (y1 * x2) % self.p
        y1y2 = (y1 * y2) % self.p
        x1x2 = (x1 * x2) % self.p
        dx1x2y1y2 = (self.d * x1x2 * y1y2) % self.p

        try:
            x3 = ((x1y2 + y1x2) * self.mod_inverse(1 + dx1x2y1y2, self.p)) % self.p
            y3 = ((y1y2 - self.a * x1x2) * self.mod_inverse(1 - dx1x2y1y2, self.p)) % self.p
        except ValueError:
            return (0, 1)

        return x3, y3

    def point_mul(self, k: int, P: Tuple[int, int]) -> Tuple[int, int]:
        """Multiply a point by a scalar"""
        result = (0, 1)
        addend = P

        while k:
            if k & 1:
                result = self.point_add(result, addend)
            addend = self.point_add(addend, addend)
            k >>= 1

        return result

    def generate_nonce(self, secret_key: int, input_point: Tuple[int, int]) -> int:
        """Generate a nonce"""
        hashed_sk = hashlib.sha512(secret_key.to_bytes(32, 'little')).digest()
        h_input = self.point_to_string(input_point)
        k_string = self.sha512(hashed_sk[32:] + h_input)
        return self.string_to_int(k_string) % self.n

    def challenge(self, Y: Tuple[int, int], I: Tuple[int, int], O: Tuple[int, int],
                  U: Tuple[int, int], V: Tuple[int, int], ad: str) -> int:
        """Generate a challenge value"""
        data = self.point_to_string(Y) + self.point_to_string(I) + self.point_to_string(O) + \
               self.point_to_string(U) + self.point_to_string(V) + ad.encode()
        return self.string_to_int(self.sha512(data))

    def generate_ticket(self, secret_key: int, input_point: Tuple[int, int], ad: str) -> Tuple[
        Tuple[int, int], Tuple[int, int]]:
        """Generate a VRF ticket"""
        O = self.point_mul(secret_key, input_point)
        Y = self.point_mul(secret_key, self.G)
        k = self.generate_nonce(secret_key, input_point)
        U, V = self.point_mul(k, self.G), self.point_mul(k, input_point)
        c = self.challenge(Y, input_point, O, U, V, ad)
        s = (k + c * secret_key) % self.n
        return O, (c, s)

    def point_neg(self, point: Tuple[int, int]) -> Tuple[int, int]:
        """Negate a point on the curve"""
        x, y = point
        return (-x % self.p, y)

    def point_subtract(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> Tuple[int, int]:
        """Subtract two points"""
        return self.point_add(p1, self.point_neg(p2))

    def verify_ticket(self, public_key: Tuple[int, int], input_point: Tuple[int, int],
                      additional_data: str, output_point: Tuple[int, int],
                      proof: Tuple[int, int]) -> bool:
        """Verify a VRF ticket"""
        c, s = proof
        U = self.point_subtract(self.point_mul(s, self.G), self.point_mul(c, public_key))
        V = self.point_subtract(self.point_mul(s, input_point), self.point_mul(c, output_point))
        return c == self.challenge(public_key, input_point, output_point, U, V, additional_data)

    def hash_to_point(self, message: str) -> int:
        """Map a message deterministically to a point on the curve"""
        hash_value = int.from_bytes(hashlib.sha256(message.encode()).digest(), 'little')
        return hash_value % self.p

    def point_to_string(self, P: Tuple[int, int]) -> bytes:
        """Convert a point to bytes"""
        x, y = P
        return x.to_bytes(32, 'little') + y.to_bytes(32, 'little')

    def string_to_int(self, s: bytes) -> int:
        """Convert bytes to an integer"""
        return int.from_bytes(s, 'little')

    def sha512(self, data: bytes) -> bytes:
        """Calculate SHA-512 hash"""
        return hashlib.sha512(data).digest()

    def select_winning_ticket(self, tickets: List[Dict]) -> Tuple[List[Dict], Dict]:
        """Select the winning ticket from valid tickets based on minimum output_point"""
        valid_tickets = [ticket for ticket in tickets if ticket['valid']]
        if not valid_tickets:
            return [], None

        winning_ticket = min(valid_tickets, key=lambda ticket: ticket['output_point'])
        return valid_tickets, winning_ticket

    def run_example(self):
        """Example usage of the IETF class"""
        tickets = []
        validators = ["Hello", "Hello Computer", "Hello Coder"]

        for i in range(len(validators)):
            secret_key = random.randint(1, self.p - 1)
            input_point= BandersnatchCurve.generate_random_point(self.hash_to_point(validators[i]))
            print(input_point)  # Print the input point

            ad = f"Ticket {i + 1}"
            output_point, proof = self.generate_ticket(secret_key, input_point, ad)
            public_key = self.point_mul(secret_key, self.G)
            valid = self.verify_ticket(public_key, input_point, ad, output_point, proof)

            tickets.append({
                'proof': proof,
                'valid': valid,
                'output_point': output_point
            })
            print(f"Ticket {i + 1}: {'VALID' if valid else 'INVALID'}")

        valid_tickets, winning_ticket = self.select_winning_ticket(tickets)

        if valid_tickets:
            print("\nValid tickets:")
            for idx, ticket in enumerate(valid_tickets, 1):
                print(f"Ticket {idx}: Proof {ticket['proof']}, Output Point: {ticket['output_point']}")

            print(f"\nWinning ticket: Proof {winning_ticket['proof']}, Output Point: {winning_ticket['output_point']}")
        else:
            print("\nNo valid tickets found.")


def main():
    """Main function to run the IETF example"""
    ietf = IETF()
    ietf.run_example()


if __name__ == "__main__":
    main()
