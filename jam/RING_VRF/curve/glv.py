from dataclasses import dataclass
from sympy import Matrix, Rational, sqrt
from typing import List, Tuple


@dataclass
class GLV_Specs:
    is_glv:bool =False
    lamda: int = 0x13b4f3dc4a39a493edf849562b38c72bcfc49db970a5056ed13d21408783df05
    constant_b: int = 0x52c9f28b828426a561f00d3a63511a882ea712770d9af4d6ee0f014d172510b4
    constant_c: int = 0x6cc624cf865457c3a97c6efd6c17d1078456abcfff36f4e9515c806cdf650b3d

    @staticmethod
    def extended_euclidean_algorithm(n: int, lam: int) -> List[Tuple[int, int, int]]:
        s0, t0, r0 = 1, 0, n
        s1, t1, r1 = 0, 1, lam
        sequence = [(s0, t0, r0), (s1, t1, r1)]

        while r1 != 0:
            q = r0 // r1
            r2 = r0 - q * r1
            s2 = s0 - q * s1
            t2 = t0 - q * t1
            sequence.append((s2, t2, r2))
            s0, t0, r0 = s1, t1, r1
            s1, t1, r1 = s2, t2, r2

        return sequence[:-1]  # Removing the last step where r = 0

    def find_short_vectors(self, n: int, lam: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        sequence = self.extended_euclidean_algorithm(n, lam)
        sqrt_n = sqrt(n)

        m = max(i for i, (_, _, r) in enumerate(sequence) if r >= sqrt_n)

        rm_plus1, tm_plus1 = sequence[m + 1][2], sequence[m + 1][1]
        v1 = (rm_plus1, -tm_plus1)

        if m + 2 < len(sequence):
            rm_plus2, tm_plus2 = sequence[m + 2][2], sequence[m + 2][1]
        else:
            rm_plus2, tm_plus2 = float('inf'), float('inf')

        v2_candidates = [(sequence[m][2], -sequence[m][1]), (rm_plus2, -tm_plus2)]
        v2 = min(v2_candidates, key=lambda v: v[0] ** 2 + v[1] ** 2)

        return v1, v2

    @staticmethod
    def compute_beta(k: int, v1: Tuple[int, int], v2: Tuple[int, int], n: int) -> Tuple[float, float]:
        det_A = v1[0] * v2[1] - v1[1] * v2[0]
        if det_A == 0:
            return 0.0, 0.0  # Handle zero determinant case

        A_inv = Matrix([[v2[1], -v2[0]], [-v1[1], v1[0]]]) * Rational(1, det_A)
        beta = A_inv * Matrix([[k], [0]])

        return float(beta[0]), float(beta[1])

    def decompose_scalar(self, k: int, v1: Tuple[int, int], v2: Tuple[int, int], n: int) -> Tuple[int, int]:
        v, b1, b2 = self.find_closest_lattice_point(k, v1, v2, n)
        k1 = (k - v[0]) % n
        k2 = (-v[1]) % n
        return k1, k2

    def find_closest_lattice_point(self, k: int, v1: Tuple[int, int], v2: Tuple[int, int], n: int):
        beta_1, beta_2 = self.compute_beta(k, v1, v2, n)

        b1 = round(beta_1)
        b2 = round(beta_2)

        v = (b1 * v1[0] + b2 * v2[0], b1 * v1[1] + b2 * v2[1])

        return v, b1, b2

