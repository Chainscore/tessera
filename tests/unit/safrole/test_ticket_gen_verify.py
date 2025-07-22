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
