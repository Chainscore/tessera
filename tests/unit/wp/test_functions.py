from math import ceil

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tsrkit_types import Bytes, ByteArray, Uint, Vector, Null

from jam.merklization import BMRFunctions, MMRFunctions
from jam.types.protocol.crypto import Ed25519Signature
from jam.types.protocol.merkle import MMR, OptionHash
from jam.types.work.report import WorkReport

from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.work.manifest import Segments, Segment
from jam.utils.constants import SEGMENT_SIZE



def zero_padding(value: ByteArray, n: Uint) -> Bytes:
    length = len(value)
    padding = n - (((length + n - 1) % n) + 1)

    cnt = 0
    for i in range(padding):
        cnt += 1
        value.append(0)

    return value


def paged_proof(segments: Segments) -> Segments:
    """
    Page Proof function P defined in Eqn 14.10
    Compiles Justifications for exported segments

    Source:
        https://graypaper.fluffylabs.dev/#/cc517d7/1b2a001b8b00?v=0.6.5
    Args:
        segments (Segments): List of exported segments
    Returns:
        Proofs of size same as segments
    """
    page_count = ceil(len(segments)/64)
    bmr = BMRFunctions()
    pages: Segments = Segments([])

    for x in range(page_count):
        path = bmr.merkle_path_fn(segments, Uint(6), Uint(x))
        leaf = bmr.leaf_page_fn(values=segments, size=Uint(6), index=Uint(x))

        merkle_path = Uint(len(path)).encode() + Vector(path).encode()
        leaf =  Uint(len(leaf)).encode() + leaf.encode()


        padded_proof = zero_padding(ByteArray(merkle_path + leaf), SEGMENT_SIZE)
        proof: Segment = Segment(padded_proof)
        pages.append(proof)

    return pages

def test_merkle():
    segments: Segments = Segments([])

    for i in range(2):
        val = f"segment {i}".encode()
        val = val.ljust(4104, b'\0')
        new_seg = Segment(val)

        segments.append(new_seg)

    bmr = BMRFunctions()


    proofs = bmr.merkle_path_fn(segments, 0, 1)

    leaves = bmr.leaf_page_fn(segments, 0, 1)

    root = bmr.cd_merkle_fn(segments)
    print(type(leaves), type(proofs))
    print(type(leaves[0]),leaves[0], type(proofs[0]))

    root_2 = verify_merkle_proof(leaves, proofs, 1)

    assert root == root_2

def test_sign():
    r = WorkReport.from_json({
                    "package_spec": {
                        "hash": "0x63c03371b9dad9f1c60473ec0326c970984e9c90c0b5ed90eba6ada471ba4d86",
                        "length": 17180,
                        "erasure_root": "0x9fc7e637969aef1a95dfb560a914cf5161a76498db3aa19df131cea199ed6e44",
                        "exports_root": "0x5c9dca800c145685f052ce1ba343e2b66b4c333ee4c4ca3b29cb347b1009cb83",
                        "exports_count": 3
                    },
                    "context": {
                        "anchor": "0x39cb518983b02695034b3b92cb31a7334e1a2ec3ef7dbfa32c68e4e8444363f1",
                        "state_root": "0xd8c577816b629241676502d0461e4eae42a375461314d64484f35f4228da23d6",
                        "beefy_root": "0xf5df0c11416d43c55b43e096572d450b7780ed0fd7b540f26c8ded8e0d41e183",
                        "lookup_anchor": "0x16bda47e5a68daf53c39ddee8af4ecaced7e87f3f0ac9da5a6f4f9e41350d319",
                        "lookup_anchor_slot": 6,
                        "prerequisites": []
                    },
                    "core_index": 0,
                    "authorizer_hash": "0x9a3a97d1950356ef6d3c20acb5ab6699be454b1498ecd513bdc6d849497e42eb",
                    "auth_output": "0x",
                    "segment_root_lookup": {},
                    "results": [
                        {
                            "service_id": 42,
                            "code_hash": "0x6470fd21983eae8d706f1edd5e2dc5afe095980f8fb7bd4ebfd33550d8730246",
                            "payload_hash": "0x3cf2d09da453bbdd6b68d8a1acd5f15ba23ba46d4ff087592b3d319432500a50",
                            "accumulate_gas": 18012,
                            "result": {
                                "ok": "0x64756d6d792d726573756c74"
                            },
                            "refine_load": {
                                "gas_used": 821,
                                "imports": 8,
                                "extrinsic_count": 8,
                                "extrinsic_size": 1526,
                                "exports": 17
                            }
                        }
                    ],
                    "auth_gas_used": 0
                })
    c = r.core_index
    # print("ff", r)
    data = c.encode() + r.encode()
    # data = r.encode()
    print("hex", data.hex())
    hash_val = Hash.blake2b(data)
    g = b"jam_guarantee"

    seed = bytes.fromhex("0500000005000000050000000500000005000000050000000500000005000000")
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    op = Ed25519Signature("939c76652641416f92ac95b886de5ab23477c41b799942d004e314ccc28e34d01c2bf266659133ae9fc0aa373ea781495b2045b646a8807ac078e885cfc2f103")
    signature = private_key.sign(g + hash_val.encode())
    # print("S", signature)
    pk = private_key.public_key()

    print("H", signature.hex())
    # pk.verify(bytes(op),g+hash_val.encode())
    assert op == Ed25519Signature(signature)

def test_beefy():
    fn = MMRFunctions()
    root = OpaqueHash("0xf5df0c11416d43c55b43e096572d450b7780ed0fd7b540f26c8ded8e0d41e183")
    # mmr = MMR(Vector([OptionHash(OpaqueHash("0x9803365d6327b01a4f40285d669f22104e9abc9962e0e8a59fc76e848039fa7f")), OptionHash(OpaqueHash("0x6629377e978ca0a8993aeb7313bce8ed2859b8c4274716a8e4960d9ef61e2d26")), OptionHash(OpaqueHash("cd17112b3055a1129cf3216edb6bf5506df9701829d694ceafa4a15a242ec763"))]))
    # new_root = fn.super_peak(mmr)
    # beefy = Hash.keccak256(mmr.encode())
    # print("check 1", new_root, new_root == root, beefy, beefy == root)
    # mmr = MMR(Vector([OptionHash(Null), OptionHash(Null), OptionHash(Null), OptionHash(OpaqueHash("0xd7cc7a7751048dbe8d0232b5d0273acd874e56c19e41a2e09b590ca00e59908d"))]))
    # new_root = fn.super_peak(mmr)
    # beefy = Hash.keccak256(mmr.encode())
    # print("check 2", new_root, new_root == root, beefy, beefy == root)
    # mmr = MMR(Vector([OptionHash(OpaqueHash("0xdbec20b48047e4efbe1accfcf35cdec640de6d676f3152590a7d47df8043c9fe")), OptionHash(Null), OptionHash(Null), OptionHash(OpaqueHash("0xd7cc7a7751048dbe8d0232b5d0273acd874e56c19e41a2e09b590ca00e59908d"))]))
    # new_root = fn.super_peak(mmr)
    # beefy = Hash.keccak256(mmr.encode())
    # print("check 3", new_root, new_root == root, beefy, beefy == root)
    # mmr = MMR(Vector([OptionHash(Null), OptionHash(OpaqueHash("0x937e03794adb6b889d9a060802f92adf879bc2032980d13a2dee2dc3cae32888")), OptionHash(Null), OptionHash(OpaqueHash("0xd7cc7a7751048dbe8d0232b5d0273acd874e56c19e41a2e09b590ca00e59908d"))]))
    # new_root = fn.super_peak(mmr)
    # beefy = Hash.keccak256(mmr.encode())
    # print("check 4", new_root, new_root == root, beefy, beefy == root)
    # mmr = MMR(Vector([OptionHash(OpaqueHash("0x7f7c99311ad62e91b08412ce30b370088a10429a38369ad433217e8bccbfff31")), OptionHash(OpaqueHash("0x937e03794adb6b889d9a060802f92adf879bc2032980d13a2dee2dc3cae32888")), OptionHash(Null), OptionHash(OpaqueHash("0xd7cc7a7751048dbe8d0232b5d0273acd874e56c19e41a2e09b590ca00e59908d"))]))
    # new_root = fn.super_peak(mmr)
    # beefy = Hash.keccak256(mmr.encode())
    # print("check 5", new_root, new_root == root, beefy, beefy == root)
    # mmr = MMR(Vector([OptionHash(Null), OptionHash(Null), OptionHash(OpaqueHash("0x7f64e54f8be039cea06582eb38e7f36f924c1f59a0f3043b4df6f140cccd6ddf")), OptionHash(OpaqueHash("0xd7cc7a7751048dbe8d0232b5d0273acd874e56c19e41a2e09b590ca00e59908d"))]))
    # new_root = fn.super_peak(mmr)
    # beefy = Hash.keccak256(mmr.encode())
    # print("check 6", new_root, new_root == root, beefy, beefy == root)
    mmr = MMR(Vector([OptionHash(OpaqueHash("0x4c31a1024d553c6f5eb90a26f9c53507d6d58b7be1197c0f86054b084353de5f")), OptionHash(Null), OptionHash(OpaqueHash("0x7f64e54f8be039cea06582eb38e7f36f924c1f59a0f3043b4df6f140cccd6ddf")), OptionHash(OpaqueHash("0xd7cc7a7751048dbe8d0232b5d0273acd874e56c19e41a2e09b590ca00e59908d"))]))
    new_root = fn.super_peak(mmr)
    beefy = Hash.keccak256(fn.encode_mmr(mmr))
    print("mmr", mmr)
    print("check 7", new_root, new_root == root, beefy, beefy == root)
    # mmr = MMR(Vector([OptionHash(Null), OptionHash(OpaqueHash("0x62dccd9f84828c1094b24271da81161386276b8804ce42c0b97e87c21b9c7f8b")), OptionHash(OpaqueHash("0x7f64e54f8be039cea06582eb38e7f36f924c1f59a0f3043b4df6f140cccd6ddf")), OptionHash(OpaqueHash("0xd7cc7a7751048dbe8d0232b5d0273acd874e56c19e41a2e09b590ca00e59908d"))]))
    # new_root = fn.super_peak(mmr)
    # beefy = Hash.keccak256(mmr.encode())
    # print("check 8", new_root, new_root == root, beefy, beefy == root)

    assert root == new_root

def verify_merkle_proof(leaves: Vector[OpaqueHash], trace: Vector[OpaqueHash],  index: int):
    bmr = BMRFunctions()
    root = bmr._node_fn(leaves)
    for sibling in reversed(trace):
        if index % 2 == 0:
            root = bmr._node_fn(Vector([root, sibling]))
        else:
            root = bmr._node_fn(Vector([sibling, root]))
        index = index // 2
    return root
