from dataclasses import dataclass
from typing import List, Optional
from .utils import NodeHash, NodeType
from tsrkit_types.bytes import Bytes


@dataclass
class Node:
    encoded: Bytes[64]  # The full 64-byte encoded value from your encoding routines.
    bit_index: Optional[int] = None  # For branch nodes, store the bit index used for splitting.
    left: Optional[NodeHash] = None  # For branch nodes, pointer to left child.
    right: Optional[NodeHash] = None  # For branch nodes, pointer to right child.

    @property
    def type(self) -> NodeType:
        # bit extraction without full conversion
        first_byte = self.encoded[0]
        if first_byte & 0x80:  # First bit is 1
            if first_byte & 0x40:  # Second bit is 1
                return NodeType.LEAF_NORMAL
            else:  # Second bit is 0
                return NodeType.LEAF_EMBEDDED
        else:  # First bit is 0
            return NodeType.BRANCH

    @property
    def key_bits_248(self) -> List[bool]:
        return self.encoded.key_bits_248()
