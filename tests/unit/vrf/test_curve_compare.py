from __future__ import annotations
from cProfile import label
import os
from pathlib import Path
import random
import time
from typing import List

import matplotlib.pyplot as plt
import pytest

from jam.ring_vrf.curve.glv import DisabledGLV
from jam.ring_vrf.curve.specs.baby_jubjub import BabyJubJub_TE_Curve, BabyJubJubPoint
from jam.ring_vrf.curve.specs.bandersnatch import (
    Bandersnatch_TE_Curve,
    BandersnatchGLVSpecs,
    BandersnatchPoint,
)
from jam.ring_vrf.curve.specs.ed25519 import Ed25519_TE_Curve, Ed25519Point
from jam.ring_vrf.curve.specs.jubjub import JubJub_TE_Curve, JubJubPoint
from jam.ring_vrf.ietf.ietf import IETF_VRF
from jam.ring_vrf.pedersen.pedersen import PedersenVRF
from tests.fixtures.utils import create_dummy_bytes

# Test data paths
TEST_DATA_DIR = Path("tests/unit/vrf/data")
ARK_VRF_DIR = TEST_DATA_DIR / "ark-vrf"
COLORFUL_NOTION_DIR = TEST_DATA_DIR / "colorful-notion"


def gen_test_secrets(n: int, seed = 0, bit_size = 256) -> List[int]:
    random.seed(seed)
    return [random.randint(2**(bit_size - 1), 2**(bit_size)) for i in range(n)]

def run_pk(runs, point, curve, bit_size = 256) -> int:
    start = time.thread_time()
    for scalar in gen_test_secrets(runs, 0, bit_size):
        # Convert secret key to scalar
        point.generator_point() * (
            scalar
            % curve.ORDER
        )
    end = time.thread_time()
    avg_time = (end - start)/runs
    # print(f"\nTime taken by {curve.__class__.__name__}\n\t{avg_time} (WA on {runs} runs)")
    return avg_time

def run_ietfvrf(runs, point, curve):
    ietf = IETF_VRF(curve, point)
    prove_time = 0
    verify_time = 0
    for scalar in gen_test_secrets(runs):
        alpha = create_dummy_bytes(32)
        ad = create_dummy_bytes(10)
        start = time.process_time()
        output_point, proof = ietf.prove(alpha, scalar, ad)
        prove_break = time.process_time()
        pub_key = point.generator_point() * (scalar % curve.ORDER)
        input_point = point.encode_to_curve(alpha, b"")
        prove_time += prove_break - start
        start = time.process_time()
        ietf.verify(
            pub_key,
            input_point,
            ad,
            output_point,
            proof,
        )
        last = time.process_time()
        verify_time += last - start

    print(f"\nTime taken by {curve.__class__.__name__} \n Prove: {(prove_time)/runs} \t Verify: {verify_time/runs} \n(WA on {runs} runs)")

def run_pedersenvrf(runs, point, curve):
    pedersen = PedersenVRF(curve, point)
    prove_time = 0
    verify_time = 0
    for scalar in gen_test_secrets(runs):
        alpha = create_dummy_bytes(32)
        ad = create_dummy_bytes(10)
        start = time.process_time()
        output_point, proof = pedersen.prove(alpha, scalar, ad, random.randint(0, 2**256))
        prove_break = time.process_time()
        pub_key = point.generator_point() * (scalar % curve.ORDER)
        input_point = point.encode_to_curve(alpha, b"")
        prove_time += prove_break - start
        start = time.process_time()
        pedersen.verify(
            input_point,
            ad,
            output_point,
            proof,
        )
        last = time.process_time()
        verify_time += last - start

    print(f"\nTime taken by {curve.__class__.__name__} \n Prove: {(prove_time)/runs} \t Verify: {verify_time/runs} \n(WA on {runs} runs)")

@pytest.mark.skipif("BENCHMARKING" not in os.environ, reason="benchmarking test")
def test_curve_mul():
    runs = 1
    times, bandersnatch_times, jj_times, ed25519_times, babyjj_times = [], [], [], [], []
    print("\nComparing Curves \t Bandersnatch \t JubJub \t Ed25519 \t Baby JubJub")
    for bit_size in range(222, 351, 1):
        times.append(bit_size)
        bandersnatch_times.append(run_pk(runs, BandersnatchPoint, Bandersnatch_TE_Curve, bit_size))
        jj_times.append(run_pk(runs, JubJubPoint, JubJub_TE_Curve, bit_size))
        ed25519_times.append(run_pk(runs, Ed25519Point, Ed25519_TE_Curve, bit_size))
        babyjj_times.append(run_pk(runs, BabyJubJubPoint, BabyJubJub_TE_Curve, bit_size))
        print(f"{bit_size} \t {bandersnatch_times[-1]} \t {jj_times[-1]} \t {ed25519_times[-1]} \t {babyjj_times[-1]}")


    plt.plot(times, bandersnatch_times, label="Bandersnatch")
    plt.plot(times, jj_times, label="JubJub")
    plt.plot(times, ed25519_times, label="Ed25519")
    plt.plot(times, babyjj_times, label="Baby JubJub")
    plt.legend()

    plt.title('GLV vs General Point Multiplication')
    plt.xlabel('Bitsize')
    plt.ylabel('Time in sec')
    plt.grid()
    plt.tight_layout()
    plt.show()

@pytest.mark.skipif("BENCHMARKING" not in os.environ, reason="benchmarking test")
def test_bandersnatch_glv():
    runs = 1
    times = []
    for bit_size in range(222, 351, 1):
        times.append(run_pk(runs, BandersnatchPoint, Bandersnatch_TE_Curve, bit_size))
    print(times)

    glv_times = [0.0482029167, 0.03979682090000001, 0.03955280000000001, 0.025961595800000015, 0.03968332499999998, 0.03347033339999998, 0.03152604169999997, 0.032462120799999994, 0.05778502909999998, 0.03333266669999997, 0.025739758400000045, 0.03793686250000006, 0.0259148916, 0.030668037500000002, 0.03193347499999995, 0.02569468749999997, 0.03795007500000001, 0.04384807500000001, 0.03205431670000003, 0.03804507090000007, 0.03765359580000007, 0.03042584159999997, 0.042861854100000055, 0.037321616700000074, 0.031124529100000055, 0.026415637500000068, 0.031384166700000014, 0.04103312920000004, 0.03142982080000003, 0.03666374589999997, 0.030601012500000024, 0.026486374999999996, 0.030784491700000062, 0.03571122500000001, 0.02606703750000001, 0.025657820800000054, 0.04075555410000007, 0.04101984170000002, 0.040803454199999936, 0.04061674590000006, 0.035693525000000115, 0.02995389589999995, 0.03562494159999989, 0.04045137909999976, 0.030798395899999775, 0.026698254200000094, 0.030998474999999814, 0.04100897090000011, 0.03141573330000007, 0.03128098329999993, 0.030846579099999973, 0.03104827080000021, 0.031433745900000074, 0.030929208399999908, 0.04083225410000004, 0.026655099999999977, 0.04611884169999989, 0.026267112500000068, 0.030341054200000172, 0.035655570799999835, 0.03591219580000029, 0.03139012919999971, 0.0255287083999999, 0.031065866699999844, 0.03592319169999989, 0.031129804200000066, 0.03083424170000022, 0.03693625839999974, 0.030661145800000254, 0.035989429099999984, 0.0265631833999997, 0.031241016699999947, 0.026279900000000113, 0.025799291600000274, 0.03097595420000019, 0.036552412500000034, 0.03140374590000015, 0.025615070799999983, 0.026144041699999933, 0.03122984169999974, 0.040238899999999946, 0.026020429100000086, 0.03589226660000015, 0.03101684579999997, 0.029895662499999885, 0.031111887500000178, 0.026101616699999754, 0.031035924999999763, 0.03132057499999981, 0.04604167080000003, 0.03542949170000007, 0.03575625410000001, 0.03571323330000027, 0.030256624999999815, 0.025778804200000137, 0.03620291249999994, 0.04077308330000022, 0.03123731250000006, 0.04064969160000018, 0.025199133299999944, 0.03130861670000016, 0.031076029199999765, 0.04068587920000013, 0.03490140830000001, 0.03086687500000025, 0.03998000420000025, 0.030993950000000582, 0.031360016700000416, 0.035602670900000535, 0.040499608399999686, 0.03611219580000054, 0.030903787500000134, 0.03057332079999995, 0.046660345800000155, 0.03164179999999987, 0.04597853750000027, 0.04123302499999966, 0.035640704200000074, 0.03611546249999975, 0.03080378330000002, 0.03629685830000042, 0.04078144169999973, 0.03548464159999938, 0.03591732909999976, 0.0354605792000001, 0.04147472920000013, 0.03565150000000017, 0.03075427500000032, 0.03148265000000024]
    wo_glv_times = [0.20997865000000004, 0.21078203329999998, 0.21224395419999995, 0.21190947089999995, 0.21262666669999994, 0.21474643330000004, 0.21475831670000006, 0.21561010419999996, 0.21656312500000005, 0.21788152909999994, 0.21842662500000004, 0.21961090419999998, 0.21992636660000003, 0.22079654170000004, 0.22168792500000017, 0.22264758749999985, 0.2234624832999998, 0.22425233750000045, 0.2255665125, 0.22668230000000023, 0.2275236458000002, 0.22878782910000056, 0.22958686250000043, 0.23054951250000003, 0.23127852500000046, 0.23225316249999964, 0.23339277080000045, 0.23422587499999992, 0.23573779159999972, 0.23583964579999872, 0.23690630830000003, 0.23873757920000002, 0.24006020000000064, 0.23798471670000082, 0.2393837957999992, 0.24030242919999978, 0.2377719082999988, 0.24102898750000037, 0.23815270000000055, 0.24033021669999927, 0.2351249750000008, 0.23738334579999928, 0.24004062919999997, 0.23600557920000115, 0.2378956708000004, 0.23846245830000043, 0.23841054170000006, 0.23882814589999982, 0.23898887919999937, 0.23836839589999953, 0.23718930830000035, 0.23912686670000055, 0.24036070420000044, 0.23927379590000014, 0.23866577080000012, 0.2364049042000019, 0.2380297165999991, 0.23633923339999968, 0.24015554169999973, 0.23574827079999922, 0.2390005790999993, 0.23874453330000164, 0.23861972079999988, 0.2389235874999997, 0.23923949999999933, 0.24022597919999952, 0.24076932910000154, 0.2392839707999997, 0.2379666749999984, 0.23965583330000015, 0.24080294579999872, 0.23972404589999882, 0.23754894999999862, 0.24035650000000147, 0.2370522582999996, 0.2388090333000008, 0.2375758542, 0.24094720839999867, 0.23968403750000106, 0.23779233749999945, 0.23633052500000246, 0.24223146250000127, 0.23778209589999905, 0.23942340829999864, 0.24139398750000113, 0.23947864579999986, 0.23789624160000072, 0.23805309999999907, 0.2395146834000002, 0.2378460082999993, 0.23720606250000173, 0.2366224791999997, 0.24034883330000129, 0.23798887089999993, 0.23735228339999992, 0.23991455410000243, 0.24007878749999917, 0.23673437090000107, 0.23816969589999815, 0.23996653329999731, 0.2367200208000014, 0.23917754159999732, 0.23926264170000025, 0.23916100420000247, 0.23948602080000114, 0.23535197920000145, 0.23609542920000023, 0.23835457090000034, 0.23863656250000248, 0.23718149590000054, 0.23762932909999676, 0.23672729169999798, 0.23967553749999979, 0.24010326670000381, 0.2425358416999984, 0.23988616659999593, 0.23740442910000184, 0.23899571250000234, 0.237931333399996, 0.23858126250000283, 0.23608920000000352, 0.2381982375000007, 0.2374387375000026, 0.2434151374999999, 0.2361722874999998, 0.23743606669999623, 0.23972686669999915, 0.2375515957999994, 0.23741117499999972]
    plt.plot([i for i in range(222, 351)], glv_times, label="With GLV")
    plt.plot([i for i in range(222, 351)], wo_glv_times, label="Without GLV")
    plt.legend()

    plt.title('GLV vs General Point Multiplication')
    plt.xlabel('Bitsize')
    plt.ylabel('Time in sec')
    plt.grid()
    plt.tight_layout()
    plt.show()

@pytest.mark.skipif("BENCHMARKING" not in os.environ, reason="benchmarking test")
def test_curve_ietf_vrf():
    runs = 1
    bandersnatch_bench = run_ietfvrf(runs, BandersnatchPoint, Bandersnatch_TE_Curve)
    jubjub_bench = run_ietfvrf(runs, JubJubPoint, JubJub_TE_Curve)
    ed25519_bench = run_ietfvrf(runs, Ed25519Point, Ed25519_TE_Curve)
    babyjub_bench = run_ietfvrf(runs, BabyJubJubPoint, BabyJubJub_TE_Curve)


@pytest.mark.skipif("BENCHMARKING" not in os.environ, reason="benchmarking test")
def test_curve_pedersen_vrf():
    runs = 1
    bandersnatch_bench = run_pedersenvrf(runs, BandersnatchPoint, Bandersnatch_TE_Curve)
    jubjub_bench = run_pedersenvrf(runs, JubJubPoint, JubJub_TE_Curve)
    ed25519_bench = run_pedersenvrf(runs, Ed25519Point, Ed25519_TE_Curve)
    babyjub_bench = run_pedersenvrf(runs, BabyJubJubPoint, BabyJubJub_TE_Curve)
