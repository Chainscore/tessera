from math import log2, ceil
from typing import Optional, Callable

from jam.types.base.sequences.vector import Vector
from jam.types.base.sequences.bytes import ByteArray32, Bytes

from jam.types.protocol.crypto import Hash, OpaqueHash

class BMRFunctions:
    """General Merklization implementation for Binary Trees as defined in Section E.1"""

    def __init__(self):
        self._ZERO_HASH = ByteArray32([0] * 32)
        self._NODE_PREFIX = bytes('node', 'utf-8')
        self._LEAF_PREFIX = bytes('leaf', 'utf-8')

    def _preprocessor_fn(
        self,
        values: Vector[Bytes],
        hash_fn: Optional[Callable[[bytes], 'ByteArray32']] = Hash.blake2b
    ) -> Vector[OpaqueHash]:
        """
        Constancy Preprocessor Function Implementation as defined in Equation E.7 in Section E.1.2

        Definition:
            (v: [Y], H: Y->H) -> o: [H]
        Args:
            values: Sequence of 32 octet blobs
            hash_fn: Hash Function
        Returns:
            Sequences of Hashes (in ByteArray32)
        """
        new_values: Vector[OpaqueHash] = Vector([])
        for val in values:
            new_val = hash_fn(self._LEAF_PREFIX + bytes(val))
            new_values.append(new_val)

        length = len(values)
        padded_length = 2 ** (ceil(log2(max(1, length))))

        for i in range(padded_length - length):
            new_values.append(self._ZERO_HASH)

        return new_values

    def _node_fn(
        self,
        values: Vector[Bytes],
        hash_fn: Optional[Callable[[bytes], 'ByteArray32']] = Hash.blake2b
    ) -> Bytes | OpaqueHash:
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
            return self._ZERO_HASH

        elif sz == 1:
            return values[0]

        else:
            mid = (sz + 1) // 2

            left = values[:mid]
            right = values[mid:]

            left_node = self._node_fn(left, hash_fn)
            right_node = self._node_fn(right, hash_fn)

            return hash_fn(self._NODE_PREFIX + bytes(left_node) + bytes(right_node))

    @staticmethod
    def _p_i(values: Vector[Bytes], index: int) -> int:
        """
        Util Function P_I Implementation for Trace Function
        """
        sz = len(values)
        mid = (sz+1) // 2

        if index < mid:
            return 0
        else:
            return mid

    @staticmethod
    def _p_bool(values: Vector[Bytes], index: int, case: bool) -> Vector[Bytes]:
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
        values: Vector[Bytes],
        index: int,
        hash_fn: Optional[Callable[[bytes], 'ByteArray32']] = Hash.blake2b
    ) -> Vector[Bytes | ByteArray32]:
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

        if sz <= 1:
            return Vector([])

        else:
            trace = Vector([])

            node = self._node_fn(self._p_bool(values, index, False))
            trace.append(Bytes(bytes(node)))

            new_ind = self._p_i(values, index)
            trace_nodes = self.trace_fn(self._p_bool(values, index,True), index - new_ind, hash_fn)

            trace.extend(trace_nodes)

            return trace

    def wb_merkle_fn(
        self,
        values: Vector[Bytes],
        hash_fn: Optional[Callable[[bytes], 'ByteArray32']] = Hash.blake2b
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
            return hash_fn(bytes(values[0]))

        else:
            return self._node_fn(values, hash_fn)

    def cd_merkle_fn(
        self,
        values: Vector[Bytes],
        hash_fn: Optional[Callable[[bytes], 'ByteArray32']] = Hash.blake2b
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
        return self._node_fn(leaves, hash_fn)

    def merkle_path_fn(
        self,
        values: Vector[Bytes],
        size: int,
        index: int,
        hash_fn: Optional[Callable[[bytes], 'ByteArray32']] = Hash.blake2b
    ) -> Vector[OpaqueHash]:
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

        val = ceil(log2(max(1, len(values))) - size)

        sz = max(0, val)
        ind = (2 ** size) * index

        leaves = self._preprocessor_fn(values, hash_fn)

        path = self.trace_fn(leaves, ind, hash_fn)
        return path[:sz]

    def leaf_page_fn(
        self,
        values: Vector[Bytes],
        size: int,
        index: int,
        hash_fn: Optional[Callable[[bytes], 'ByteArray32']] = Hash.blake2b
    ) -> Vector[Bytes]:
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

        page: Vector[Bytes] = Vector([])


        ind = (2 ** size) * index
        val = min(ind + 2 ** size, len(values))

        for i in range(ind, val):
            page.append(Bytes(hash_fn(self._LEAF_PREFIX + bytes(values[i]))))

        return page

    def verify_proof(self, trace: Vector[OpaqueHash], leaves: Vector[OpaqueHash], leaf_index: int, og_root: OpaqueHash) -> bool:
        """
        Merkle Proof Verification Function (not provided in GP)

        Args:
            trace: Sequence of nodes depicting path of a tree to a particular index
            leaves: Sequence of leaf nodes
            leaf_index: Node Index
            og_root: Previous root to match proof with
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

        return og_root == root