from math import ceil

from jam.merklization import BMRFunctions
from jam.types import Int, Bytes, Byte, Vector, ByteArray32
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
