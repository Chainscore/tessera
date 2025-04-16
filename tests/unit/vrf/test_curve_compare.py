from __future__ import annotations
from pathlib import Path
import random
import time
from typing import List

from jam.ring_vrf.curve.specs.baby_jubjub import BabyJubJub_TE_Curve, BabyJubJubPoint
from jam.ring_vrf.curve.specs.bandersnatch import (
    Bandersnatch_TE_Curve,
    BandersnatchPoint,
)
from jam.ring_vrf.curve.specs.ed25519 import Ed25519_TE_Curve, Ed25519Point
from jam.ring_vrf.curve.specs.jubjub import JubJub_TE_Curve, JubJubPoint
from jam.ring_vrf.ietf.ietf import IETF_VRF
from tests.fixtures.utils import create_dummy_bytes

# Test data paths
TEST_DATA_DIR = Path("tests/unit/vrf/data")
ARK_VRF_DIR = TEST_DATA_DIR / "ark-vrf"
COLORFUL_NOTION_DIR = TEST_DATA_DIR / "colorful-notion"


def gen_test_secrets(n: int, seed = 0) -> List[int]:
    random.seed(seed)
    return [random.randint(0, 2**256) for i in range(n)]

def run_pk(runs, point, curve) -> int:
    start = time.process_time()
    for scalar in gen_test_secrets(runs):
        # Convert secret key to scalar
        point.generator_point() * (
            scalar
            % curve.ORDER
        )
    end = time.process_time()
    print(f"\nTime taken by {curve.__class__.__name__}\n\t{(end - start)/runs} (WA on {runs} runs)")

def run_ietfvrf(runs, point, curve) -> int:
    ietf = IETF_VRF(curve, point)
    prove_time = 0
    verify_time = 0
    for scalar in gen_test_secrets(runs):
        start = time()
        alpha = create_dummy_bytes(32)
        ad = create_dummy_bytes(10)
        output_point, proof = ietf.prove(alpha, scalar, ad)
        prove_break = time()
        pub_key = point.generator_point() * (scalar % curve.ORDER)
        input_point = point.encode_to_curve(alpha, b"")
        prove_time += prove_break - start
        start = time()
        ietf.verify(
            pub_key,
            input_point,
            ad,
            output_point,
            proof,
        )
        last = time()
        verify_time += last - start

    print(f"\nTime taken by {curve.__class__.__name__} \n Prove: {(prove_time)/runs} \t Verify: {verify_time/runs} \n(WA on {runs} runs)")


def test_curve_mul():
    bandersnatch_bench = run_pk(10, BandersnatchPoint, Bandersnatch_TE_Curve)
    jubjub_bench = run_pk(10, JubJubPoint, JubJub_TE_Curve)
    ed25519_bench = run_pk(10, Ed25519Point, Ed25519_TE_Curve)
    babyjub_bench = run_pk(10, BabyJubJubPoint, BabyJubJub_TE_Curve)

# def test_curve_ietf_vrf():
#     bandersnatch_bench = run_ietfvrf(1, BandersnatchPoint, Bandersnatch_TE_Curve)
#     jubjub_bench = run_ietfvrf(1, JubJubPoint, JubJub_TE_Curve)
#     ed25519_bench = run_ietfvrf(1, Ed25519Point, Ed25519_TE_Curve)
#     babyjub_bench = run_ietfvrf(1, BabyJubJubPoint, BabyJubJub_TE_Curve)
