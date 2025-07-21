from dataclasses import dataclass
from typing import List, Optional
from jam.state.merkle.utils import NodeHash, NodeType
from tsrkit_types.bytes import Bytes


@dataclass
class Node:
    encoded: Bytes[64]  # The full 64-byte encoded value from your encoding routines.
    bit_index: Optional[
        int
    ] = None  # For branch nodes, store the bit index used for splitting.
    left: Optional[NodeHash] = None  # For branch nodes, pointer to left child.
    right: Optional[NodeHash] = None  # For branch nodes, pointer to right child.

    @property
    def type(self) -> NodeType:
        first_byte = self.encoded.to_bits()
        if first_byte[0] and first_byte[1]:
            return NodeType.LEAF_NORMAL
        elif first_byte[0] and not first_byte[1]:
            return NodeType.LEAF_EMBEDDED
        elif not first_byte[0]:
            return NodeType.BRANCH
        else:
            raise ValueError(f"Invalid encoded node - {self.encoded}")

    @property
    def key_bits_248(self) -> List[bool]:
        return Bytes(self.encoded).to_bits()[8:256]
