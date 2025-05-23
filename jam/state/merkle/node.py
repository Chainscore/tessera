from dataclasses import dataclass
from typing import List, Optional
from jam.state.merkle.utils import NodeHash, NodeType
from jam.types.base.sequences.bytes import ByteArray64
from jam.utils.byte_utils import ByteUtils

@dataclass
class Node:
    encoded: ByteArray64                # The full 64-byte encoded value from your encoding routines.
    bit_index: Optional[int] = None     # For branch nodes, store the bit index used for splitting.
    left: Optional[NodeHash] = None     # For branch nodes, pointer to left child.
    right: Optional[NodeHash] = None    # For branch nodes, pointer to right child.

    @property
    def type(self) -> NodeType:
        first_byte = ByteUtils.bytes_to_bitarray(bytes(self.encoded[0]))
        if first_byte==[1,1,0,0,0,0,0,0]:
            return NodeType.LEAF_NORMAL
        elif first_byte[0]==1 and first_byte[1]==0:
            return NodeType.LEAF_EMBEDDED
        elif first_byte[0]==0:
            return NodeType.BRANCH
        
    @property
    def key_bits_248(self) -> List[int|bool]:
        return ByteUtils.bytes_to_bitarray(bytes(self.encoded)[1:32])