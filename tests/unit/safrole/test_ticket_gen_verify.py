# import pytest
# from dot_ring.vrf.ring.ring_vrf import RingVrf
# from py_ark_vrf import secret_from_seed, verify_ring, public_from_le_secret

# from jam.settings import Settings


# @pytest.mark.parametrize("vals,idx", [([0, 1, 2, 3, 4, 5], 1)])
# def test_tickets_generation(vals: list[int], idx: int):
#     producer, secret = secret_from_seed(int(vals[idx]).to_bytes(32))
#     keys = [secret_from_seed(int(s).to_bytes(32))[0] for s in vals]
#     alpha = b"alpha"
#     ad = b"ad"
#     proof = RingVrf.ring_vrf_proof(alpha, ad, secret, producer, keys, False)

#     assert verify_ring(alpha, proof, keys, ad)

#     # False positive
#     assert not verify_ring(b"beta", proof, keys, ad)

# def test_debug_ticket_1():
#     # alpha = bytes.fromhex("6a616d5f7469636b65745f7365616cbb30a42c1e62f0afda5f0a4e8a562f7a13a24cea00ee81917b86b89e801314aa00")
#     alpha = b'jam_ticket_seal\xbb0\xa4,\x1eb\xf0\xaf\xda_\nN\x8aV/z\x13\xa2L\xea\x00\xee\x81\x91{\x86\xb8\x9e\x80\x13\x14\xaa\x00'
#     ad = b''
#     # secret = bytes.fromhex("007596986419e027e65499cc87027a236bf4a78b5e8bd7f675759d73e7a9c799")
#     secret = b"\x00u\x96\x98d\x19\xe0'\xe6T\x99\xcc\x87\x02z#k\xf4\xa7\x8b^\x8b\xd7\xf6uu\x9ds\xe7\xa9\xc7\x99"
#     _, sk = secret_from_seed(secret)
#     # producer = bytes.fromhex("db9657a7d2ee3d4b9031cfc8ba85623b8cb7bfe2a0a059136eef24085c2071e2")
#     producer = b'\xffq\xc6\xc0?\xf8\x8a\xdb^\xd5,\x96\x81\xde\x16)\xa5Np/\xc1G)\xf6\xb5\r/\nv\xf1\x85\xb3'
#     # vals = ['ff71c6c03ff88adb5ed52c9681de1629a54e702fc14729f6b50d2f0a76f185b3', 'dee6d555b82024f1ccf8a1e37e60fa60fd40b1958c4bb3006af78647950e1b91', '9326edb21e5541717fde24ec085000b28709847b8aab1ac51f84e94b37ca1b66', '0746846d17469fb2f95ef365efcab9f4e22fa1feb53111c995376be8019981cc', '151e5c8fe2b9d8a606966a79edd2f9e5db47e83947ce368ccba53bf6ba20a40b', '2105650944fcd101621fd5bb3124c9fd191d114b7ad936c1d79d734f9f21392e']
#     keys = [b'\xffq\xc6\xc0?\xf8\x8a\xdb^\xd5,\x96\x81\xde\x16)\xa5Np/\xc1G)\xf6\xb5\r/\nv\xf1\x85\xb3',
#      b'\xde\xe6\xd5U\xb8 $\xf1\xcc\xf8\xa1\xe3~`\xfa`\xfd@\xb1\x95\x8cK\xb3\x00j\xf7\x86G\x95\x0e\x1b\x91',
#      b'\x93&\xed\xb2\x1eUAq\x7f\xde$\xec\x08P\x00\xb2\x87\t\x84{\x8a\xab\x1a\xc5\x1f\x84\xe9K7\xca\x1bf',
#      b'\x07F\x84m\x17F\x9f\xb2\xf9^\xf3e\xef\xca\xb9\xf4\xe2/\xa1\xfe\xb51\x11\xc9\x957k\xe8\x01\x99\x81\xcc',
#      b'\x15\x1e\\\x8f\xe2\xb9\xd8\xa6\x06\x96jy\xed\xd2\xf9\xe5\xdbG\xe89G\xce6\x8c\xcb\xa5;\xf6\xba \xa4\x0b',
#      b'!\x05e\tD\xfc\xd1\x01b\x1f\xd5\xbb1$\xc9\xfd\x19\x1d\x11Kz\xd96\xc1\xd7\x9dsO\x9f!9.']
#     # keys = [bytes.fromhex(v) for v in vals]
#     proof = RingVrf.ring_vrf_proof(
#         alpha, ad, sk, producer, keys, False
#     )
#
#     assert verify_ring(alpha, proof, keys, ad)
#
#     # False positive
#     assert not verify_ring(b"beta", proof, keys, ad)