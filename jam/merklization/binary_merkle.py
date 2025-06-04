from math import log2, ceil
from typing import Optional, Callable

from tsrkit_types.choice import Choice
from tsrkit_types.integers import Uint
from tsrkit_types.option import Option
from tsrkit_types.sequences import Vector
from tsrkit_types.bytes import Bytes

from jam.types.protocol.crypto import Hash, OpaqueHash

class BMRFunctions:
    """General Merklization implementation for Binary Trees as defined in Section E.1"""

    def __init__(self):
        self._ZERO_HASH = Bytes[32]([0] * 32)
        self._NODE_PREFIX = bytes('node', 'utf-8')
        self._LEAF_PREFIX = bytes('leaf', 'utf-8')

    def _preprocessor_fn(
        self,
        values: Vector[Bytes],
        hash_fn: Optional[Callable[[bytes], 'Bytes[32]']] = Hash.blake2b
    ) -> Vector[OpaqueHash]:
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
        new_values: Vector[OpaqueHash] = Vector([])
        for val in values:
            new_val = hash_fn(self._LEAF_PREFIX + bytes(val))
            new_values.append(new_val)

        return new_values

    def _node_fn(
        self,
        values: Vector[Bytes],
        hash_fn: Optional[Callable[[bytes], 'Bytes[32]']] = Hash.blake2b
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
            return hash_fn(self._NODE_PREFIX + bytes(self._node_fn(left, hash_fn)) + bytes(self._node_fn(right, hash_fn)))

    @staticmethod
    def _p_i(values: Vector[Bytes], index: Uint) -> Uint:
        """
        Util Function P_I Implementation for Trace Function
        """
        sz = len(values)
        mid = (sz+1) // 2

        if index < mid:
            return Uint(0)
        else:
            return Uint(mid)

    @staticmethod
    def _p_bool(values: Vector[Bytes], index: Uint, case: bool) -> Vector[Bytes]:
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

    def _trace_fn(
        self,
        values: Vector[Bytes],
        index: Uint,
        hash_fn: Optional[Callable[[bytes], 'Bytes[32]']] = Hash.blake2b
    ) -> Vector[Choice[Bytes, Bytes[32]]]:
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
            trace.append(node)

            new_ind = self._p_i(values, index)
            trace_nodes = self._trace_fn(self._p_bool(values, index,True), index - int(new_ind), hash_fn)

            trace.extend(trace_nodes)

            return trace

    def wb_merkle_fn(
        self,
        values: Vector[Bytes],
        hash_fn: Optional[Callable[[bytes], 'Bytes[32]']] = Hash.blake2b
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
        hash_fn: Optional[Callable[[bytes], 'Bytes[32]']] = Hash.blake2b
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

        return self._node_fn(self._preprocessor_fn(values, hash_fn), hash_fn)

    def merkle_path_fn(
        self,
        values: Vector[Bytes],
        size: Uint,
        index: Uint,
        hash_fn: Optional[Callable[[bytes], 'Bytes[32]']] = Hash.blake2b
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

        val = ceil(log2(max(1, len(values))) - int(size))

        sz = max(0, val)
        ind = (2 ** int(size)) * index

        leaves = self._preprocessor_fn(values, hash_fn)

        path = self._trace_fn(leaves, ind, hash_fn)
        return path[:sz]

    def leaf_page_fn(
        self,
        values: Vector[Bytes],
        size: Uint,
        index: Uint,
        hash_fn: Optional[Callable[[bytes], 'Bytes[32]']] = Hash.blake2b
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

        page: Vector[OpaqueHash] = Vector([])


        ind = (2 ** int(size)) * index
        val = min(ind + 2 ** int(size), len(values))

        for i in range(ind, val):
            page.append(hash_fn(self._LEAF_PREFIX + bytes(values[i])))

        return page
