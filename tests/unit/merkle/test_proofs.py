from math import ceil, log2
from typing import Optional

from tsrkit_types import Vector, Uint, ByteArray, TypedVector, structure, Bytes

from jam.merklization.binary_merkle import ChoicedHashes, BMRFunctions ,OpaqueHashes
from jam.types import Hash
from jam.types.work.manifest import Segments, Segment
from jam.types.protocol.core import SegmentRoot, OpaqueHash

from jam.utils.dummy.utils import create_dummy_bytes4104
from jam.utils.constants import SEGMENT_SIZE

_ZERO_HASH = Bytes[32]([0] * 32)
_NODE_PREFIX = Bytes('node', 'utf-8')
_LEAF_PREFIX = Bytes('leaf', 'utf-8')

NODES: ChoicedHashes = ChoicedHashes([])

@structure
class SegmentVector:
    segments: Segments
    proofs: Segments
    segment_root: SegmentRoot
    paths: TypedVector[ChoicedHashes]
    leaves: TypedVector[Vector[OpaqueHash]]
    nodes: ChoicedHashes
    whole_traces: TypedVector[ChoicedHashes]
    processed_leaves: Vector[OpaqueHash]
    single_proofs: TypedVector[ChoicedHashes]


def zero_padding(value: ByteArray, n: Uint):
    length = len(value)
    padding = n - (((length + n - 1) % n) + 1)

    for i in range(padding):
        value.append(0)

    return value

def preprocessor_fn(
    values: TypedVector[Bytes],
    hash_fn = Hash.blake2b
) -> OpaqueHashes:
    new_values = OpaqueHashes([])
    for val in values:
        new_val = hash_fn(_LEAF_PREFIX + Bytes(val))
        new_values.append(new_val)

    length = len(values)
    padded_length = 2 ** (ceil(log2(max(1, length))))

    for i in range(padded_length - length):
        new_values.append(_ZERO_HASH)

    return new_values

def trace_fn(
    values: TypedVector[Bytes],
    index: Uint,
    hash_fn = Hash.blake2b
) -> ChoicedHashes:
    merklizer = BMRFunctions()
    sz = len(values)

    trace = ChoicedHashes([])

    if sz <= 1:
        return trace

    else:
        global NODES

        node = merklizer._node_fn(merklizer._p_bool(values, index, False))
        NODES.append(node)

        trace.append(node)

        new_ind = merklizer._p_i(values, index)
        trace_nodes = trace_fn(merklizer._p_bool(values, index,True), index - new_ind, hash_fn)
        trace.extend(trace_nodes)
        return trace

def test_paged_proof():
    merklizer = BMRFunctions()

    segments : Segments = Segments([Segment(create_dummy_bytes4104()) for _ in range(144)])
    # print("\n")
    # for i, s in enumerate(segments):
    #     print("Segment", i, s.hex())

    leaves = merklizer._preprocessor_fn(segments)
    node = merklizer._node_fn(leaves)
    seg_root = OpaqueHash(node.unwrap())

    page_count = ceil(len(segments) / 64)

    paths = TypedVector[ChoicedHashes]([])
    leaves = TypedVector[Vector[OpaqueHash]]([])

    pages: Segments = Segments([])
    whole_traces: TypedVector[ChoicedHashes] = TypedVector[ChoicedHashes]([])

    for x in range(page_count):
        # path = merklizer.merkle_path_fn(values=segments, size=Uint(6), index=Uint(x))
        values = segments
        size = Uint(6)
        index = Uint(x)

        if index >= len(values):
            raise IndexError("index out of range")

        val = ceil(log2(max(1, len(values))) - int(size))

        sz = max(0, val)
        ind = (2 ** size) * index

        oleaves = preprocessor_fn(values)

        opath = trace_fn(oleaves, ind)

        path = ChoicedHashes(opath[:sz])
        whole_trace = ChoicedHashes(opath)
        whole_traces.append(whole_trace)

        paths.append(path)


        leaf = merklizer.leaf_page_fn(values=segments, size=Uint(6), index=Uint(x))
        leaves.append(leaf)

        merkle_path = bytes(len(path)) + path.encode()
        leaf = bytes(len(leaf)) + leaf.encode()

        segment_proof = Segment(zero_padding(ByteArray(merkle_path + leaf), SEGMENT_SIZE))
        pages.append(segment_proof)

    proofs = pages

    single_proofs = TypedVector[ChoicedHashes]([])
    for i in range(6):
        single_proof = merklizer.merkle_path_fn(segments, Uint(0), Uint(i))
        single_proofs.append(single_proof)

    global NODES

    vector = SegmentVector(
        segments,
        proofs,
        seg_root,
        paths,
        leaves,
        NODES,
        whole_traces,
        oleaves,
        single_proofs
    )

    from jam.utils.benchmark import write_json
    write_json("../../../vectors/proofs", vector.to_json())

