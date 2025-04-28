from dataclasses import dataclass
from typing import Optional, Literal
from jam.types.base.sequences.bytes import ByteArray32, ByteArray64, Bytes
from jam.state.merkle.trie import NodeHash

# Allowed types for DB node objects.
DBNodeType = Literal["branch", "leaf_embedded", "leaf_normal", "empty"]

@dataclass
class DBNode:
    node_type: DBNodeType            # "branch", "leaf_embedded", "leaf_normal", or "empty"
    encoded: ByteArray64             # The full 64-byte encoded value from your encoding routines.
    key: Optional[ByteArray32] = None  # For leaf nodes, store the key only.
    bit_index: Optional[int] = None    # For branch nodes, store the bit index used for splitting.
    left: Optional[NodeHash] = None    # For branch nodes, pointer to left child.
    right: Optional[NodeHash] = None   # For branch nodes, pointer to right child.
