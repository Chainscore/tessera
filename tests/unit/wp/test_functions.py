from copy import deepcopy
from math import ceil
from time import time
from typing import Optional

from jam.merklization import BMRFunctions
from jam.types import Int, Bytes, Byte, Vector, ByteArray32
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.work.manifest import Segments, Segment, ByteArray4104
from jam.utils.constants import SEGMENT_SIZE



def zero_padding(value: Bytes, n: int) -> Bytes:
    length = len(value)
    padding = n - (((length + n - 1) % n) + 1)

    print("dwef", length)
    cnt = 0
    for i in range(padding):
        cnt += 1
        value.append(Byte(0))

    print("run", cnt, padding)
    return value

def test_padding():
    # i = ByteArray("0x8720b97ddd6acc0f6eb66e095524038675a4e4067adc10ec39939eaefc47d842")
    # i = ByteArray(b"\0x1\0x2\0x3")
    i = Bytes(123)
    n = Int(7)

    print(f"input {i}")

    # wp = WorkPackageProcessing()

    o = zero_padding(i, n)

    # eo = ByteArray("0x1111100")
    # print(f"expected {eo}")
    print(f"output {o}")


def test_mb():
    i1 = Bytes("0x461236a7eb29dcffc1dd282ce1de0e0ed691fc80e91e02276fe8f778f088a1b8")
    i2 = Bytes("0xe7cb536522c1c1b41fff8021055b774e929530941ea12c10f1213c56455f29ad")
    i3 = Bytes("0xb0a487a4adf6a0eda5d69ddd2f8b241cf44204f0ff793e993e5e553b7862a1dc")
    i4 = Bytes("0x3e5d0bea78537414bd1cfdaeb0f22d743bcaba5dbffacbabce8457f4cd78f69b")
    i5 = Bytes("0xb7f8dffa65971832ec9e19719debc04b1ccd9ad27187a4943807ca756962481b")

    v: Vector[Bytes] = Vector([i1, i2, i3, i4, i5])
    # v: Vector[Bytes] = Vector([i1, i2, i3])

    bmr = BMRFunctions()
    op = 0
    # op = bmr.wb_merkle_fn(v)
    # 0xe10b77e2d9708e38e009af1a84d20c0570d5a748fbef5f5cf197730d7996c948

    # op = bmr.cd_merkle_fn(v)
    # 0x165953484f6b286e273a2932eb2dd0221feedd2ab61ff167823bbdadddcc1199

    # op = bmr.leaf_page_fn(v, 1, 0)
    # Vector([0x8d556e635ef8f6a7f97e9cea15bea981130c41dced0ba2caa87c1ecbf26f0c81,0x7f05fbf2d279e583ab1f6889c460920ab0ff7c062b56bdf358576910826a8a8d])

    # op = bmr.leaf_page_fn(v, 1, 1)
    # Vector([0x6818ecd5a12f3993471d07f8f7793cc033455bdd5378f8862e40945cef3539a8, 0xd49e47badc5d8785aa1745d6268874ccee04d9b1a5ebbbca7dff3a64c7c61070])

    # op = bmr.leaf_page_fn(v, 1, 2)
    # Vector([0xd70c5c1c466aa2f9e7ccaa41b194cbb5ad169e1c18d7b06f55be6664a3c40fb8])

    # op = bmr.merkle_path_fn(v, 0, 0)
    # [0x974c999813e81ed9f37fe5ca46dea122694abd5f129ee4574b4eb66d4a9feac1, 0x6818ecd5a12f3993471d07f8f7793cc033455bdd5378f8862e40945cef3539a8]
    # [0x974c999813e81ed9f37fe5ca46dea122694abd5f129ee4574b4eb66d4a9feac1, 0x6818ecd5a12f3993471d07f8f7793cc033455bdd5378f8862e40945cef3539a8, 0x7f05fbf2d279e583ab1f6889c460920ab0ff7c062b56bdf358576910826a8a8d]

    # op = bmr._trace_fn(v, 0)
    # Vector([0xa3d5f48b6b23c308d80b4ff9d9f02fffd5183460848b0288d45a20b608d25808, 0xa3d5f48b6b23c308d80b4ff9d9f02fffd5183460848b0288d45a20b608d25808, 0xa3d5f48b6b23c308d80b4ff9d9f02fffd5183460848b0288d45a20b608d25808])

    print(f"op {op}")

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
    print("cnt", page_count)
    bmr = BMRFunctions()
    pages: Segments = Segments([])
    print("segs ", len(segments))
    for x in range(page_count):
        print("x", x)
        path = bmr.merkle_path_fn(segments, Int(6), Int(x))
        print("path", len(path), path)
        leaf = bmr.leaf_page_fn(values=segments, size=Int(6), index=Int(x))

        print("leaves", len(leaf), leaf)
        print("--------------------------------------------")
        merkle_path = Int(len(path)).encode() + Vector(path).encode()
        leaf =  Int(len(leaf)).encode() + leaf.encode()

        concat = merkle_path + leaf
        print("len", len(merkle_path), len(leaf))
        print("concated ", concat)

        print("hhh", len(Bytes(merkle_path+leaf)))
        padded_proof = zero_padding(Bytes(merkle_path + leaf), SEGMENT_SIZE)
        print("padded proof", len(padded_proof), padded_proof)
        proof: Segment = Segment(padded_proof)
        print(f"proof is {proof}")
        pages.append(proof)

        print(f"proof {x}", proof)
    return pages

def test_merkle():
    segments: Segments = Segments([])

    start_time = time()
    for i in range(2):
        val = f"segment {i}".encode()
        val = val.ljust(4104, b'\0')
        new_seg = Segment(ByteArray4104(val))

        segments.append(new_seg)

    end_time = time()
    execution_time = end_time - start_time
    print("Execution time for building segments:", execution_time, "seconds")


    bmr = BMRFunctions()

    # node_root = bmr.wb_merkle_fn(segments)
    # print("node root", node_root)

    start_time = time()
    proofs = bmr.merkle_path_fn(segments, Int(0), Int(1))
    print("proof pages", len(proofs), proofs)
    end_time = time()
    execution_time = end_time - start_time
    print("Execution time:", execution_time, "seconds")

    start_time = time()
    leaves = bmr.leaf_page_fn(segments, Int(0), Int(1))
    print("leaves pages", len(leaves), leaves)
    end_time = time()
    execution_time = end_time - start_time
    print("Execution time:", execution_time, "seconds")
    #
    #
    root = bmr.cd_merkle_fn(segments)
    print(f"root {root}")
    #

    verify_merkle_proof(leaves, proofs, root, 1)


def verify_merkle_proof(leaves: Vector[OpaqueHash], trace: Vector[OpaqueHash], og_root: OpaqueHash, index: int) -> bool:
    bmr = BMRFunctions()


    start_time = time()
    root = bmr._node_fn(leaves)
    for sibling in reversed(trace):
        if index % 2 == 0:
            root = bmr._node_fn(Vector([root, sibling]))
        else:
            root = bmr._node_fn(Vector([sibling, root]))
        index = index // 2
    print("Root Check", og_root == root)
    end_time = time()
    execution_time = end_time - start_time
    print("Execution time for validating proofs:", execution_time, "seconds")
    return og_root == root


