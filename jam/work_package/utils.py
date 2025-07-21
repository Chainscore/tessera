from math import ceil

from tsrkit_types import ByteArray, Bytes

from jam.merklization import BMRFunctions
from jam.merklization.binary_merkle import OpaqueHashes

from jam.types.protocol import OpaqueHash
from jam.types.work.manifest import Segments, Segment

from jam.utils.constants import SEGMENT_SIZE


class Utils:
    """Utility class for handling paged proofs"""

    @staticmethod
    def zero_padding(value: ByteArray, n: int):
        """
        Zero Padding function P defined in Eqn 14.18
        Ensures that the length of individual byte array becomes a multiple of a given integer n.

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1c1a021c4902?v=0.7.0
        Args:
            value (ByteArray) : Octet Array to be padded.
            n (Int) : The target block size
        Returns:
            Padded Bytearray (length in multiple of n)
        """

        length = len(value)
        padding = n - (((length + n - 1) % n) + 1)

        for i in range(padding):
            value.append(0)

        return value

    def paged_proof(self, segments: Segments ) -> Segments:
        """
        Page Proof function P defined in Eqn 14.11
        Compiles Justifications for exported segments

        Source:
            https://graypaper.fluffylabs.dev/#/38c4e62/1b34021baa02?v=0.7.0
        Args:
            segments (Segments): List of exported segments
        Returns:
            Proofs of size same as segments
        """

        from jam.merklization.binary_merkle import BMRFunctions
        merklizer = BMRFunctions()

        subtree_depth = 6
        page_size = 2 ** subtree_depth
        page_count = ceil(len(segments) / page_size)


        pages: Segments = Segments([])
        for x in range(page_count):
            trace = merklizer.subtree_path(values=segments, page_depth=subtree_depth, index=x).unwrap32()
            leaves = merklizer.subtree_leaves(values=segments, page_depth=subtree_depth, index=x)

            proof = trace.encode() + leaves.encode()
            proof_segment = Segment(self.zero_padding(ByteArray(proof), SEGMENT_SIZE))
            pages.append(proof_segment)

        return pages

    @staticmethod
    def decode_proof(proof: Segment):
        """Function to fetch trace and leaves from a paged proof"""

        buffer = ByteArray(proof)

        trace, offset = OpaqueHashes.decode_from(buffer)
        leaves, _ = OpaqueHashes.decode_from(buffer, offset)

        return trace, leaves

    def verify_page(self, page: Segment, page_index: int, expected_root: OpaqueHash) -> bool:
        """Function to verify a merkle proof"""

        merklizer = BMRFunctions()

        trace, leaves = self.decode_proof(page)

        root = merklizer.verify_cd_tree(trace, leaves, page_index)

        return root == expected_root

    def zero_depth_proof(self, proof: Segment, segment_index: int) -> tuple[Segment, OpaqueHashes]:
        """
        Function to convert proof of depth 6 into a proof of depth 0

        Args:
            proof: Page Proof of Size 2 ** 6 ~ 64 leaves
            segment_index: Index to the segment to be proved (w.r.t original order)
        Returns:
             Zero Depth Proof
        """

        merklizer = BMRFunctions()

        subtree_depth = 6
        page_size = 2 ** subtree_depth

        sub_page_index = segment_index % page_size

        trace, leaves = self.decode_proof(proof)

        padded_leaves = leaves
        for k in range(page_size - len(leaves)):
            padded_leaves.append(Bytes[32](32))

        sub_trace = merklizer.trace_fn(padded_leaves, sub_page_index).unwrap32()
        sub_leaves = OpaqueHashes([leaves[sub_page_index]])

        trace.extend(sub_trace)

        buffer = trace.encode() + sub_leaves.encode()
        proof = Segment(self.zero_padding(ByteArray(buffer), SEGMENT_SIZE))

        return proof, trace
