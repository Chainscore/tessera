import pytest
from dot_ring.vrf.ring.ring_vrf import RingVrf
from py_ark_vrf import secret_from_seed, verify_ring, public_from_le_secret

from jam.settings import Settings


@pytest.mark.parametrize("vals,idx", [([0, 1, 2, 3, 4, 5], 1)])
def test_tickets_generation(vals: list[int], idx: int):
    producer, secret = secret_from_seed(int(vals[idx]).to_bytes(32))
    keys = [secret_from_seed(int(s).to_bytes(32))[0] for s in vals]
    alpha = b"alpha"
    ad = b"ad"
    proof = RingVrf.ring_vrf_proof(alpha, ad, secret, producer, keys, False)

    assert verify_ring(alpha, proof, keys, ad)

    # False positive
    assert not verify_ring(b"beta", proof, keys, ad)

# def test_debug_ticket_1():
#     alpha = bytes.fromhex("6a616d5f7469636b65745f7365616cbb30a42c1e62f0afda5f0a4e8a562f7a13a24cea00ee81917b86b89e801314aa00")
#     ad = b''
#     secret = bytes.fromhex("007596986419e027e65499cc87027a236bf4a78b5e8bd7f675759d73e7a9c799")
#     producer = bytes.fromhex("db9657a7d2ee3d4b9031cfc8ba85623b8cb7bfe2a0a059136eef24085c2071e2")
#     vals = ['ff71c6c03ff88adb5ed52c9681de1629a54e702fc14729f6b50d2f0a76f185b3', 'dee6d555b82024f1ccf8a1e37e60fa60fd40b1958c4bb3006af78647950e1b91', '9326edb21e5541717fde24ec085000b28709847b8aab1ac51f84e94b37ca1b66', '0746846d17469fb2f95ef365efcab9f4e22fa1feb53111c995376be8019981cc', '151e5c8fe2b9d8a606966a79edd2f9e5db47e83947ce368ccba53bf6ba20a40b', '2105650944fcd101621fd5bb3124c9fd191d114b7ad936c1d79d734f9f21392e']
#
#     keys = [bytes.fromhex(v) for v in vals]
#     proof = RingVrf.ring_vrf_proof(
#         alpha, ad, secret, producer, keys, False
#     )
#
#     assert verify_ring(alpha, proof, keys, ad)
#
#     # False positive
#     assert not verify_ring(b"beta", proof, keys, ad)