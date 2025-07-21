from __future__ import annotations

# from jam.ring_vrf.ring_proof.short_weierstrass.curve import ShortWeierstrassCurve as sw
from jam.ring_vrf.ring_proof.constants import SeedPoint
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Sequence, Any

from jam.ring_vrf.ring_proof.constants import (
    S_PRIME,
    OMEGA,
    D_512 as D,
    SIZE,
    D_2048,
)

from jam.ring_vrf.ring_proof.polynomial.ops import (
    vect_add,
    vect_sub,
    vect_mul,
    poly_evaluate,
    lagrange_basis_polynomial,
)


def _to_radix4(vec: Sequence[int]) -> List[int]:
    """Convert a radix‑2 evaluation vector to radix‑4"""
    return [poly_evaluate(vec, x, S_PRIME) for x in D_2048]


_NOT_LAST = vect_sub(D_2048, pow(OMEGA, 508, S_PRIME), S_PRIME)

_L0_RAD4: List[int]
_LN4_RAD4: List[int]

_l0_coeffs = lagrange_basis_polynomial(D, 0)
_L0_RAD4 = [poly_evaluate(_l0_coeffs, x, S_PRIME) for x in D_2048]

_ln4_coeffs = lagrange_basis_polynomial(D, SIZE - 4)
_LN4_RAD4 = [poly_evaluate(_ln4_coeffs, x, S_PRIME) for x in D_2048]


def _shift(vec: Sequence[int]) -> List[int]:
    """Rotate vector right by 4 (≈ multiply index by ω)."""
    return list(vec[4:]) + list(vec[:4])


@dataclass(slots=True)
class RingConstraintBuilder:
    """Compute c₁ₓ … c₇ₓ evaluation vectors from column evaluations."""

    Result_plus_Seed: Any
    # radix‑2 evaluation vectors coming from Column objects
    px: Sequence[int]
    py: Sequence[int]
    s: Sequence[int]
    b: Sequence[int]
    acc_x: Sequence[int]
    acc_y: Sequence[int]
    acc_ip: Sequence[int]

    # internal caches
    _cache: Dict[str, List[int]] = field(default_factory=dict, init=False)

    # radix‑4 conversions (filled in __post_init__)
    _px4: List[int] = field(init=False, repr=False)
    _py4: List[int] = field(init=False, repr=False)
    _s4: List[int] = field(init=False, repr=False)
    _b4: List[int] = field(init=False, repr=False)
    _accx4: List[int] = field(init=False, repr=False)
    _accy4: List[int] = field(init=False, repr=False)
    _accip4: List[int] = field(init=False, repr=False)

    def __post_init__(self):
        self._px4 = _to_radix4(self.px)
        self._py4 = _to_radix4(self.py)
        self._s4 = _to_radix4(self.s)
        self._b4 = _to_radix4(self.b)
        self._accx4 = _to_radix4(self.acc_x)
        self._accy4 = _to_radix4(self.acc_y)
        self._accip4 = _to_radix4(self.acc_ip)

    # convenient classmethod for Column builders
    @classmethod
    def from_columns(
        cls, columns: Mapping[str, Sequence[int]]
    ) -> "RingConstraintBuilder":
        return cls(
            acc_ip=columns["accip"],
            b=columns["b"],
            s=columns["s"],
            acc_x=columns["accx"],
            acc_y=columns["accy"],
            px=columns["Px"],
            py=columns["Py"],
        )

    def compute(self) -> Dict[str, List[int]]:
        return {
            "c1x": self._c1(),
            "c2x": self._c2()[0],
            "c3x": self._c2()[1],
            "c4x": self._c4(),
            "c5x": self._c5()[0],
            "c6x": self._c5()[1],
            "c7x": self._c7(),
        }

    compute_all = compute  # alias

    def _c1(self) -> List[int]:
        if "c1x" in self._cache:
            return self._cache["c1x"]
        accip_w = _shift(self._accip4)
        constraint = vect_sub(
            vect_sub(accip_w, self._accip4, S_PRIME),
            vect_mul(self._b4, self._s4, S_PRIME),
            S_PRIME,
        )
        c1x = vect_mul(constraint, _NOT_LAST, S_PRIME)
        self._cache["c1x"] = c1x
        return c1x

    def _c2(self) -> List[List[int]]:
        if "c2x" in self._cache:
            return [self._cache["c2x"], self._cache["c3x"]]
        bx = self._b4
        one_m_bx = vect_sub(1, bx, S_PRIME)
        accx_w = _shift(self._accx4)
        accy_w = _shift(self._accy4)
        accx_m_px = vect_sub(self._accx4, self._px4, S_PRIME)
        accx_m_px_sq = vect_mul(accx_m_px, accx_m_px, S_PRIME)
        py_m_accy = vect_sub(self._py4, self._accy4, S_PRIME)
        accx_w_m_accx = vect_sub(accx_w, self._accx4, S_PRIME)
        term1 = vect_mul(
            accx_m_px_sq,
            vect_add(vect_add(self._accx4, self._px4, S_PRIME), accx_w, S_PRIME),
            S_PRIME,
        )
        term2 = vect_mul(py_m_accy, py_m_accy, S_PRIME)
        c2_base = vect_add(
            vect_mul(bx, vect_sub(term1, term2, S_PRIME), S_PRIME),
            vect_mul(one_m_bx, vect_sub(accy_w, self._accy4, S_PRIME), S_PRIME),
            S_PRIME,
        )
        c2x = vect_mul(c2_base, _NOT_LAST, S_PRIME)
        c3_base = vect_add(
            vect_mul(
                bx,
                vect_sub(
                    vect_mul(
                        accx_m_px, vect_add(accy_w, self._accy4, S_PRIME), S_PRIME
                    ),
                    vect_mul(py_m_accy, accx_w_m_accx, S_PRIME),
                    S_PRIME,
                ),
                S_PRIME,
            ),
            vect_mul(one_m_bx, accx_w_m_accx, S_PRIME),
            S_PRIME,
        )
        c3x = vect_mul(c3_base, _NOT_LAST, S_PRIME)
        self._cache.update({"c2x": c2x, "c3x": c3x})
        return [c2x, c3x]

    def _c4(self) -> List[int]:
        if "c4x" in self._cache:
            return self._cache["c4x"]
        one_m_bx = vect_sub(1, self._b4, S_PRIME)
        c4x = vect_mul(self._b4, one_m_bx, S_PRIME)
        self._cache["c4x"] = c4x
        return c4x

    def _c5(self) -> List[List[int]]:
        if "c5x" in self._cache:
            return [self._cache["c5x"], self._cache["c6x"]]
        # seed_x, seed_y = sw.from_twisted_edwards(SeedPoint)
        seed_x, seed_y = SeedPoint

        # print("seed_here",(seed_x, seed_y))

        rx_psx, ry_psy = self.Result_plus_Seed

        # print("result here:", rx_psx, ry_psy)

        c5x = vect_add(
            vect_mul(vect_sub(self._accx4, seed_x, S_PRIME), _L0_RAD4, S_PRIME),
            vect_mul(vect_sub(self._accx4, rx_psx, S_PRIME), _LN4_RAD4, S_PRIME),
            S_PRIME,
        )

        c6x = vect_add(
            vect_mul(vect_sub(self._accy4, seed_y, S_PRIME), _L0_RAD4, S_PRIME),
            vect_mul(vect_sub(self._accy4, ry_psy, S_PRIME), _LN4_RAD4, S_PRIME),
            S_PRIME,
        )
        self._cache.update({"c5x": c5x, "c6x": c6x})
        return [c5x, c6x]

    def _c7(self) -> List[int]:
        if "c7x" in self._cache:
            return self._cache["c7x"]
        c7x = vect_add(
            vect_mul(self._accip4, _L0_RAD4, S_PRIME),
            vect_mul(vect_sub(self._accip4, 1, S_PRIME), _LN4_RAD4, S_PRIME),
            S_PRIME,
        )
        self._cache["c7x"] = c7x
        return c7x


__all__ = ["RingConstraintBuilder"]
