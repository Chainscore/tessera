from math import log2, ceil
from typing import Optional, Callable

from tsrkit_types.choice import Choice
from tsrkit_types.integers import Uint
from tsrkit_types.bytes import Bytes, Bytes32
from tsrkit_types.sequences import Vector, TypedVector

from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.utils.chainspec import chain_config

ChoicedHash = Choice[Bytes, Bytes[32]]
OpaqueHashes = TypedVector[OpaqueHash]


class ChoicedHashes(TypedVector[ChoicedHash]):
    def unwrap(self) -> TypedVector[Bytes]:
        res = TypedVector[Bytes]([])
        for val in self:
            res.append(Bytes(val.unwrap()))

        return res

    def unwrap32(self) -> OpaqueHashes:
        res = OpaqueHashes([])
        for val in self:
            value = val.unwrap()
            if getattr(value, "_length", 0) != 32:
                raise TypeError(f"Expected Bytes[32]. Got {type(value)}")
            res.append(Bytes[32](value))

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
            (v: [B], H: B->H) -> o: [H]
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
            (v: [Bn], H: Y->H) -> o: Bn U H
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

            left_node = self._node_fn(left, hash_fn).unwrap()
            right_node = self._node_fn(right, hash_fn).unwrap()

            node_val = hash_fn(self._NODE_PREFIX + left_node + right_node)

            return ChoicedHash(node_val)

    @staticmethod
    def _p_i(values: TypedVector[Bytes], index: int) -> int:
        """
        Util Function P_I Implementation for Trace Function
        This function return new start index of the subtree values where the value might lie.
        """

        sz = len(values)
        mid = (sz + 1) // 2

        if index < mid:
            return 0
        else:
            return mid

    @staticmethod
    def _p_bool(
        values: TypedVector[Bytes], index: int, case: bool
    ) -> TypedVector[Bytes]:
        """
        Util Function P_s Implementation for Trace Function
        This function returns the new set of values for given index based on
        whether it is in the subtree or is in adjacent subtree.
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
        index: int,
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> ChoicedHashes:
        """
        Trace Function Implementation as defined in Equation E.2
        Returns each opposite node from top to bottom as the tree is navigated to
        arrive at some leaf corresponding to the item of a given index into the sequence.

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
            trace_nodes = self.trace_fn(
                self._p_bool(values, index, True), index - new_ind, hash_fn
            )
            trace.extend(trace_nodes)
            return trace

    def wb_merklize(
        self,
        values: TypedVector[Bytes],
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> OpaqueHash:
        """
        Well Balanced Binary Merkle Function, MB, Implementation as defined in Equation E.3 in Section E.1.1

        Definition:
            (v: [B], H: B->H) -> o: H
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

    def cd_merklize(
        self,
        values: TypedVector[Bytes],
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> OpaqueHash:
        """
        Constant Depth Binary Merkle Function, M, Implementation as defined in Equation E.4 in Section E.1.2

        Definition:
            (v: [B], H: B->H) -> o: H
        Args:
            values: Sequence of octet blobs
            hash_fn: Hash Function
        Returns:
            32 octet Hash Root
        """

        leaves = self._preprocessor_fn(values, hash_fn)
        node = self._node_fn(leaves, hash_fn)
        return OpaqueHash(node.unwrap())

    def subtree_path(
        self,
        values: TypedVector[Bytes],
        page_depth: int,
        index: int,
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> ChoicedHashes:
        """
        Page Merkle Path Function Implementation as defined in Equation E.5

        Args:
            values: Sequence of octet blobs
            index: Node Index
            hash_fn: Hash Function
            page_depth: page size = 2 ^ page_depth
        Returns:
            Merkle path to a single page
        """

        if index >= len(values):
            raise IndexError("index out of range")

        val = ceil(log2(max(1, len(values))) - int(page_depth))

        sz = max(0, val)
        ind = (2**page_depth) * index

        leaves = self._preprocessor_fn(values, hash_fn)

        path = self.trace_fn(leaves, ind, hash_fn)
        return ChoicedHashes(path[:sz])

    def subtree_leaves(
        self,
        values: TypedVector[Bytes],
        page_depth: int,
        index: int,
        hash_fn: Optional[Callable[[Bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> TypedVector[OpaqueHash]:
        """
        Leaves Page Function Implementation as defined in Equation E.6

        Args:
            values: Sequence of octet blobs
            index: Node Index
            hash_fn: Hash Function
            page_depth: page size = 2 ^ page_depth
        Returns:
            Single page of leaves
        """

        if index >= len(values):
            raise IndexError("index out of range")

        page = TypedVector[OpaqueHash]([])

        ind = (2**page_depth) * index
        val = min(ind + 2**page_depth, len(values))

        for i in range(ind, val):
            page.append(hash_fn(self._LEAF_PREFIX + Bytes(values[i])))

        return page

    def reconstruct_root(
        self,
        leaf_index: int,
        trace: TypedVector[Bytes],
        leaf: Bytes,
        total_nodes: int,
        curr_index: int = 0,
        hash_fn: Optional[Callable[[bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> OpaqueHash:
        """
        Verifies the Merkle justification by reconstructing the Merkle root (not provided in GP)

        Args:
            leaf_index: The original index of the leaf in the full vector
            trace: Merkle path to the given leaf
            leaf: The leaf value being verified (raw bytes)
            total_nodes: Total number of nodes
            curr_index: current iteration index
            hash_fn: Hash function used in the tree

        Returns:
            The reconstructed Merkle root (OpaqueHash)
        """

        if curr_index == len(trace):
            return leaf

        mid = ceil(total_nodes / 2)
        sibling = trace[curr_index]

        curr_index += 1

        if leaf_index >= mid:
            adjusted_length = Uint(total_nodes - mid)
            index = Uint(leaf_index - mid)
            child_hash = self.reconstruct_root(
                index, trace, leaf, adjusted_length, curr_index
            )
            return hash_fn(self._NODE_PREFIX + sibling + child_hash)
        else:
            adjusted_length = Uint(total_nodes - mid)
            child_hash = self.reconstruct_root(
                leaf_index, trace, leaf, adjusted_length, curr_index
            )
            return hash_fn(self._NODE_PREFIX + child_hash + sibling)

    def verify_wb_tree(
        self,
        leaf: Bytes,
        erasure_root: Bytes,
        index: int,
        justification: TypedVector[Bytes],
        hash_fn: Optional[Callable[[bytes], "Bytes[32]"]] = Hash.blake2b,
    ) -> bool:
        """
        Merkle Proof Verification Function for Well-Balanced Tree (not provided in GP)

        Args:
            leaf: The leaf value being verified (raw bytes)
            erasure_root:
            index: The original index of the leaf in the full vector
            justification: Vector of MerkleByte (sibling hashes along path)
            hash_fn: Hash function used in the tree

        Returns:
            Verification Result
        """

        verification_root = self.reconstruct_root(
            index, justification, leaf, chain_config.num_validators, hash_fn=hash_fn
        )
        return verification_root == erasure_root

    def verify_cd_tree(
        self, trace: OpaqueHashes, leaves: OpaqueHashes, page_index: int
    ) -> OpaqueHash:
        """
        Merkle Proof Verification Function for constant depth tree (not provided in GP)

        Args:
            trace: Sequence of nodes depicting path of a tree to a particular index
            leaves: leaf nodes to prove
            page_index: Nodes Page Index
        Returns:
            Verification Result
        Note:
            In case order / depth of subtree is 0, length of leaves would be 1
            and starting root will be that leaf itself
        """

        root = self._node_fn(leaves).unwrap()
        for sibling in reversed(trace):
            if page_index % 2 == 0:
                root = self._node_fn(TypedVector([root, sibling])).unwrap()
            else:
                root = self._node_fn(TypedVector([sibling, root])).unwrap()

            page_index = page_index // 2

        return OpaqueHash(root)
