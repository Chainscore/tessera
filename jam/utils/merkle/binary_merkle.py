from math import log2, ceil
from typing import Optional, Callable

from tsrkit_types import Bytes, TypedVector
from tsrkit_types.choice import Choice
from tsrkit_types.integers import Uint
from tsrkit_types.sequences import Vector

from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.utils.dummy.utils import create_dummy_bytes


ChoicedHash = Choice[Bytes, Bytes[32]]
OpaqueHashes = TypedVector[OpaqueHash]


class ChoicedHashes(TypedVector[ChoicedHash]):

    def unwrap(self) -> TypedVector[Bytes]:
        res = TypedVector[Bytes]([])
        for val in self:
            res.append(Bytes(val.unwrap()))

        return res


class BMRFunctions:
    """General Merklization implementation for Binary Trees as defined in Section E.1"""

    def __init__(self):
        self._ZERO_HASH = Bytes[32]([0] * 32)
        self._NODE_PREFIX = Bytes("node", "utf-8")
        self._LEAF_PREFIX = Bytes("leaf", "utf-8")

    def _preprocessor_fn(
        self,
        values: TypedVector[Bytes],
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> OpaqueHashes:
        """
        Constancy Preprocessor Function Implementation as defined in Equation E.7 in Section E.1.2

        Definition:
            (v: [Y], H: Y->H) -> o: [H]
        Args:
            values: Sequence of 32 octet blobs
            hash_fn: Hash Function
        Returns:
            Sequences of Hashes (in Bytes[32])
        """
        new_values = OpaqueHashes([])
        for val in values:
            new_val = hash_fn(self._LEAF_PREFIX + Bytes(val))
            new_values.append(new_val)

        length = len(values)
        padded_length = 2 ** (ceil(log2(max(1, length))))

        for i in range(padded_length - length):
            new_values.append(self._ZERO_HASH)

        return new_values

    def _node_fn(
        self,
        values: TypedVector[Bytes],
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> ChoicedHash:
        """
        Node Function Implementation as defined in Equation E.1

        Definition:
            (v: [Yn], H: Y->H) -> o: Yn U H
        Args:
            values: Sequence of octet blobs
            hash_fn: Hash Function
        Returns:
            32 octet blob or Hash for a node
        """
        sz = len(values)

        if sz == 0:
            return ChoicedHash(self._ZERO_HASH)

        elif sz == 1:
            return ChoicedHash(values[0])

        else:
            mid = (sz + 1) // 2

            left = values[:mid]
            right = values[mid:]

            left_node = self._node_fn(left, hash_fn)
            right_node = self._node_fn(right, hash_fn)

            node_val = hash_fn(self._NODE_PREFIX + left_node.encode() + right_node.encode())
            return ChoicedHash(node_val)

    @staticmethod
    def _p_i(values: TypedVector[Bytes], index: Uint) -> Uint:
        """
        Util Function P_I Implementation for Trace Function
        """
        sz = len(values)
        mid = (sz + 1) // 2

        if index < mid:
            return Uint(0)
        else:
            return Uint(mid)

    @staticmethod
    def _p_bool(values: TypedVector[Bytes], index: Uint, case: bool) -> TypedVector[Bytes]:
        """
        Util Function P_s Implementation for Trace Function
        """
        sz = len(values)
        mid = (sz + 1) // 2
        if (index < mid) == case:
            left = values[:mid]
            return left
        else:
            right = values[mid:]
            return right

    def trace_fn(
        self,
        values: TypedVector[Bytes],
        index: Uint,
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> ChoicedHashes:
        """
        Trace Function Implementation as defined in Equation E.2

        Args:
            values: Sequence of octet blobs
            index: Node Index
            hash_fn: Hash Function
        Returns:
            Vector of corresponding path nodes
        """
        sz = len(values)

        trace = ChoicedHashes([])

        if sz <= 1:
            return trace

        else:
            node = self._node_fn(self._p_bool(values, index, False))
            trace.append(node)

            new_ind = self._p_i(values, index)
            trace_nodes = self.trace_fn(self._p_bool(values, index, True), index - new_ind, hash_fn)
            trace.extend(trace_nodes)
            return trace

    def wb_merkle_fn(
        self,
        values: TypedVector[Bytes],
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> OpaqueHash:
        """
        Well Balanced Binary Merkle Function Implementation as defined in Equation E.3 in Section E.1.1

        Definition:
            (v: [Y], H: Y->H) -> o: H
        Args:
            values: Sequence of octet blobs
            hash_fn: Hash Function
        Returns:
            32 octet Hash Root
        """
        if len(values) == 1:
            return hash_fn(values[0])

        else:
            node = self._node_fn(values, hash_fn)
            return OpaqueHash(node.unwrap())

    def cd_merkle_fn(
        self,
        values: TypedVector[Bytes],
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> OpaqueHash:
        """
        Constant Depth Binary Merkle Function Implementation as defined in Equation E.4 in Section E.1.2

        Definition:
            (v: [Y], H: Y->H) -> o: H
        Args:
            values: Sequence of octet blobs
            hash_fn: Hash Function
        Returns:
            32 octet Hash Root
        """

        leaves = self._preprocessor_fn(values, hash_fn)
        node = self._node_fn(leaves, hash_fn)
        return OpaqueHash(node.unwrap())

    def merkle_path_fn(
        self,
        values: TypedVector[Bytes],
        size: Uint,
        index: Uint,
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> ChoicedHashes:
        """
        Page Merkle Path Function Implementation as defined in Equation E.5

        Args:
            values: Sequence of octet blobs
            index: Node Index
            hash_fn: Hash Function
            size: page size = 2 ^ size
        Returns:
            Merkle path to a single page
        """
        if index >= len(values):
            raise IndexError("index out of range")

        val = ceil(log2(max(1, len(values))) - int(size))

        sz = max(0, val)
        ind = (2**size) * index

        leaves = self._preprocessor_fn(values, hash_fn)

        path = self.trace_fn(leaves, ind, hash_fn)
        return ChoicedHashes(path[:sz])

    def leaf_page_fn(
        self,
        values: TypedVector[Bytes],
        size: Uint,
        index: Uint,
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> Vector[OpaqueHash]:
        """
        Leaves Page Function Implementation as defined in Equation E.6

        Args:
            values: Sequence of octet blobs
            index: Node Index
            hash_fn: Hash Function
            size: page size = 2 ^ size
        Returns:
            Single page of leaves
        """
        if index >= len(values):
            raise IndexError("index out of range")

        page = Vector[OpaqueHash]([])

        ind = (2**size) * index
        val = min(ind + 2**size, len(values))

        for i in range(ind, val):
            page.append(hash_fn(self._LEAF_PREFIX + Bytes(values[i])))

        return page

    def verify_proof(
        self, trace: Vector[OpaqueHash], leaves: Vector[OpaqueHash], leaf_index: int
    ) -> OpaqueHash:
        """
        Merkle Proof Verification Function for Well-Balanced Tree (not provided in GP)

        Args:
            trace: Sequence of nodes depicting path of a tree to a particular index
            leaves: Sequence of leaf nodes
            leaf_index: Node Index
        Returns:
            Verification Result
        """

        root = self._node_fn(leaves)
        for sibling in reversed(trace):
            if leaf_index % 2 == 0:
                root = self._node_fn(Vector([root, sibling]))
            else:
                root = self._node_fn(Vector([sibling, root]))
            leaf_index = leaf_index // 2

        return root

    # def verify_constant_proof(self, leaf_slice: Vector[OpaqueHash], page_index: int, x: int, trace: Vector[OpaqueHash], expected_root: OpaqueHash):
    #     """
    #         Verify constant-depth Merkle proof (𝓜 + 𝓛ₓ + 𝒥ₓ)
    #         - leaf_slice: list of hashed leaves from 𝓛ₓ (2^x items)
    #         - page_index: which 2^x block this is
    #         - x: log2 of page size (e.g., x=2 for 4-leaf pages)
    #         - trace: Merkle trace from 𝒥ₓ (log2(n) - x items)
    #         - expected_root: the full root to compare against
    #         """
    #     # Build the subtree root for this page
    #     nodes = leaf_slice
    #     while len(nodes) > 1:
    #         new_level = []
    #         for i in range(0, len(nodes), 2):
    #             left = nodes[i]
    #             right = nodes[i + 1] if i + 1 < len(nodes) else b'\x00' * 32
    #             new_level.append(self._node_fn(Vector([left, right])))
    #         nodes = new_level
    #     subtree_root = nodes[0]
    #
    #     index = page_index
    #     current_hash = subtree_root
    #     for sibling in trace:
    #         if index % 2 == 0:
    #             current_hash = self._node_fn(Vector([current_hash, sibling]))
    #         else:
    #             current_hash = self._node_fn(Vector([sibling, current_hash]))
    #         index //= 2
    #     return current_hash == expected_root

    def verify_wb_merkle(
        self,
        leaf: Bytes,
        index: Uint,
        justification: Vector[ChoicedHash],
        hash_fn: Optional[Callable[[bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> OpaqueHash:
        """
        Verifies the Merkle justification by reconstructing the Merkle root.

        Args:
            leaf: The leaf value being verified (raw bytes)
            index: The original index of the leaf in the full vector
            justification: Vector of MerkleByte (sibling hashes along path)
            hash_fn: Hash function used in the tree

        Returns:
            The reconstructed Merkle root (OpaqueHash)
        """
        # Start from the hash of the leaf
        current_hash = leaf
        justification = reversed(justification)
        for sibling in justification:
            sibling = sibling.unwrap()
            if index % 2 == 0:
                current_hash = hash_fn(self._NODE_PREFIX + current_hash.encode() + sibling.encode())
            else:
                current_hash = hash_fn(self._NODE_PREFIX + sibling.encode() + current_hash.encode())

            index = index // 2

        return current_hash


def check_verify():
    merkle = BMRFunctions()
    temp = Vector([])
    for i in range(0, 15):
        temp.append(Bytes(create_dummy_bytes(32)))

    root = merkle.wb_merkle_fn(temp)
    justification = merkle.trace_fn(temp, Uint(2))

    verified_root = merkle.verify_wb_merkle(temp[2], Uint(2), justification)
    print(
        "whether original root and verified root is correct or not:",
        verified_root == root,
    )
    assert root == verified_root
