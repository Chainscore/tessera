from math import ceil

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jam.merklization import BMRFunctions
from jam.types.base.integers.general import Int
from jam.types.base.sequences.bytes.bytes import Bytes, Byte
from jam.types.protocol.crypto import Ed25519Signature
from jam.types.work.report import WorkReport
from jam.types.base.sequences.vector import Vector

from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.work.manifest import Segments, Segment, ByteArray4104
from jam.utils.constants import SEGMENT_SIZE



def zero_padding(value: Bytes, n: int) -> Bytes:
    length = len(value)
    padding = n - (((length + n - 1) % n) + 1)

    cnt = 0
    for i in range(padding):
        cnt += 1
        value.append(Byte(0))

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
        path = bmr.merkle_path_fn(segments, Int(6), Int(x))
        leaf = bmr.leaf_page_fn(values=segments, size=Int(6), index=Int(x))

        merkle_path = Int(len(path)).encode() + Vector(path).encode()
        leaf =  Int(len(leaf)).encode() + leaf.encode()


        padded_proof = zero_padding(Bytes(merkle_path + leaf), SEGMENT_SIZE)
        proof: Segment = Segment(padded_proof)
        pages.append(proof)

    return pages

def test_merkle():
    segments: Segments = Segments([])

    for i in range(2):
        val = f"segment {i}".encode()
        val = val.ljust(4104, b'\0')
        new_seg = Segment(ByteArray4104(val))

        segments.append(new_seg)

    bmr = BMRFunctions()


    proofs = bmr.merkle_path_fn(segments, 0, 1)

    leaves = bmr.leaf_page_fn(segments, 0, 1)

    root = bmr.cd_merkle_fn(segments)
    print(type(leaves), type(proofs))
    print(type(leaves[0]),leaves[0], type(proofs[0]))

    root_2 = verify_merkle_proof(leaves, proofs, 1)

    assert root == root_2

def sign_check():
    r = WorkReport.from_json({
                    "package_spec": {
                        "hash": "0x63c03371b9dad9f1c60473ec0326c970984e9c90c0b5ed90eba6ada471ba4d86",
                        "length": 17180,
                        "erasure_root": "0x9fc7e637969aef1a95dfb560a914cf5161a76498db3aa19df131cea199ed6e44",
                        "exports_root": "0x5c9dca800c145685f052ce1ba343e2b66b4c333ee4c4ca3b29cb347b1009cb83",
                        "exports_count": 3
                    },
                    "context": {
                        "anchor": "0x6900f39559232990f5e2c1353ee2316b063604a07bdf14322dbc0188f76b4d3f",
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
    # data = c.encode() + r.encode()
    data = r.encode()
    hash_val = Hash.blake2b(data)
    g = b"jam_guarantee"

    seed = bytes.fromhex("0100000001000000010000000100000001000000010000000100000001000000")
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    op = Ed25519Signature("0xa63e201f64dc34afd0612079f140e3b6e1fc93cec3386acf17d09f863a558eadaf703cd32a30d1d52726915f12c61fddfe78f00d86c3d7470acdfa58bf1a4b09")
    signature = private_key.sign(g + hash_val.encode())
    # print("S", signature)
    pk = private_key.public_key()

    print("H", signature.hex())
    # pk.verify(bytes(op),g+hash_val.encode())
    # assert op == Ed25519Signature(signature)


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
