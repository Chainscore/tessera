from jam.ring_vrf.curve.glv import GLV_Specs
from typing import List
import math
from dataclasses import  dataclass
import hashlib
import random


@dataclass
class Curve:
    PRIME_FIELD: int
    ORDER: int
    GENERATOR_X: int
    GENERATOR_Y: int
    COFACTOR: int
    glv: GLV_Specs
    # Used for Encoding to Curve
    m = 1
    k = 128

    SUITE_STRING = "Bandersnatch_SHA-512_ELL2"
    DST = ("ECVRF_"+"Bandersnatch_XMD:SHA-512_ELL2_RO_"+ SUITE_STRING).encode()

    def calc_l(self):
        L = math.ceil((math.ceil(math.log2(self.PRIME_FIELD)) + self.k) / 8)
        return L

    @property
    def L(self):
        return self.calc_l()

    def hash_to_field(self, msg: str, count: int) -> List[int]:

        len_in_bytes = count * self.m * self.L

        # Step 2: Expand the message
        uniform_bytes = self.expand_message_xmd(msg, len_in_bytes)

        # Step 3: Convert uniform_bytes to field elements
        u_values = []
        for i in range(count):
            for j in range(self.m):
                elm_offset = self.L * (j + i * self.m)
                tv = uniform_bytes[elm_offset:elm_offset + self.L]
                e_j = self.OS2IP(tv) % self.PRIME_FIELD  # Convert bytes to integer and reduce mod p
                u_values.append(e_j)

            # Store each field element tuple

        # print("Hash to field:",u_values)

        # Step 4: Return the computed field elements
        return u_values



    def expand_message_xmd(self, msg, len_in_bytes:int) -> bytes:

        hash_fn = hashlib.sha512
        b_in_bytes = hash_fn().digest_size
        s_in_bytes = hash_fn().block_size

        ell = math.ceil(len_in_bytes / b_in_bytes)

        if ell > 255 or len_in_bytes > 65535 or len(self.DST) > 255:
            raise ValueError("Invalid input size parameters")

        DST_prime = self.DST + self.I2OSP(len(self.DST), 1)

        Z_pad = self.I2OSP(0, self.calc_l())

        l_i_b_str = self.I2OSP(len_in_bytes, 2)

        msg_prime = Z_pad + msg + l_i_b_str + self.I2OSP(0, 1) + DST_prime

        b_0 = hash_fn(msg_prime).digest()

        b_1 = hash_fn(b_0 + self.I2OSP(1, 1) + DST_prime).digest()

        b_values = [b_1]
        for i in range(2, ell + 1):
            b_i = hash_fn(self.strxor(b_0, b_values[-1]) + self.I2OSP(i, 1) + DST_prime).digest()
            b_values.append(b_i)

        uniform_bytes = b''.join(b_values)

        return uniform_bytes[:len_in_bytes]



    # Inferface to be implemented by each curve
    def map_to_curve(self, u):
        ...


    @staticmethod
    def CMOV(a:int, b:int, cond:int)->int:
        """Constant-time conditional move: if cond is True, return b; else return a."""
        return b if cond else a

    @staticmethod
    def sgn0(x:int)->int:
        """Return the sign of x: 1 if odd, 0 if even."""
        return x % 2



    def find_z_ell2(self) -> int:

        ctr = 18886178867200960497001835917649091219057080094937609519140440539760939937304  # generator value :0x664197ccb667315e6064e4ee81ad8c3586d5dcba508b7d150f3e12da9e666c2a
        while True:
            for z_cand in (ctr % self.PRIME_FIELD, -ctr % self.PRIME_FIELD):
                if not self.is_square(z_cand):
                    # print(z_cand)
                    # print("expec:",18886178867200960497001835917649091219057080094937609519140440539760939937304)
                    return z_cand
            ctr += 1


    def is_square(self,val:int)->bool:
        if val == 0:
            return True
        return pow(val, (self.PRIME_FIELD - 1) // 2, self.PRIME_FIELD)==1


    def mod_sqrt(self,a:int)->int:
        if a == 0:
            return 0
        if not self.is_square(a):
            raise ValueError("No square root exists")

        q = self.PRIME_FIELD - 1
        s = 0
        while q % 2 == 0:
            q //= 2
            s += 1

        if s == 1:
            return pow(a, (self.PRIME_FIELD + 1) // 4, self.PRIME_FIELD)

        z = 2
        while self.is_square(z):
            z += 1

        m = s
        c = pow(z, q, self.PRIME_FIELD)
        t = pow(a, q, self.PRIME_FIELD)
        r = pow(a, (q + 1) // 2, self.PRIME_FIELD)


        while t != 1:
            i = 0
            temp = t
            while temp != 1:
                temp = (temp * temp) % self.PRIME_FIELD
                i += 1
                if i == m:
                    return 0

            b = pow(c, 1 << (m - i - 1), self.PRIME_FIELD)
            m = i
            c = (b * b) % self.PRIME_FIELD
            t = (t * c) % self.PRIME_FIELD
            r = (r * b) % self.PRIME_FIELD

        return r


    @staticmethod
    def generate_random_point() -> int:
        return random.randint(1, Curve.PRIME_FIELD - 1)


    @staticmethod
    def sha512(data: bytes) -> bytes:
        """Calculate SHA-512 hash"""
        return hashlib.sha512(data).digest()


    @staticmethod
    def I2OSP(value:int, length:int)->bytes:
        if value >= 256 ** length:
            raise ValueError("integer too large")
        return value.to_bytes(length, 'big')


    @staticmethod
    def OS2IP(octets:bytearray)->int:
        return int.from_bytes(octets, 'big')


    @staticmethod
    def strxor(s1:bytes, s2:bytes)->bytes:
        return bytes(a ^ b for a, b in zip(s1, s2))



