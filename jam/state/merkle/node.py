from typing import Optional

from jam.types.base.byte import Byte
from jam.types.base.bytes import Bytes
from jam.types.protocol.crypto import Hash
from jam.types.base.sequences.byte_array import ByteArray32, ByteArray64

class Node:
    """Node encoding for Merkle trees as defined in D.2.1
    
    Nodes are fixed in size at 512 bit (64 bytes). Each node is either a branch or a leaf.
    The first bit discriminates between these two types.
    """
    
    NODE_SIZE = 64  # 512 bits
    ZERO_HASH = ByteArray32([0] * 32)  # H₀
    
    def __init__(self, hash_function: Optional[Hash] = None):
        """Initialize node encoder with optional hash function"""
        self.hash_function = hash_function or Hash.blake2b
    
    def encode_branch(self, left_hash: ByteArray32, right_hash: ByteArray32) -> ByteArray64:
        """Encode a branch node (B function in D.3)
        
        For a branch, the remaining 511 bits are split between the two child node hashes,
        using the last 255 bits of the 0-bit (left) sub-trie identity and 
        the full 256 bits of the 1-bit (right) sub-trie identity.
        """
        # Convert ByteArray32 to bytes for bitwise operations
        # Replace first bit with 0
        left_hash[0].set_bits(0, 0)
        
        # Combine the left and right hashes
        node = ByteArray64([0] * 64)
        node[0:32] = left_hash
        node[32:64] = right_hash
        
        return node

    def encode_leaf(self, key: ByteArray32, value: Bytes) -> ByteArray64:
        """Encode a leaf node (L function in D.4)
        
        For a leaf, the second bit discriminates between embedded-value leaves and regular leaves.
        For embedded values (|v| ≤ 32):
            - 6 bits store the embedded value size
            - First 31 bytes store key
            - Last 32 bytes store the value (zero-padded)
        For regular leaves:
            - 6 bits are zeroed
            - First 31 bytes store key
            - Last 32 bytes store hash of value
        """
        # First bit is 1 for leaf nodes
        node = ByteArray64([0] * 64)  # 512 bits total, first bit set
        # Set first 31 bytes of key to 1:32
        node[0].set_bits(0, 1)
        node[1:32] = key[:31]
        
        if len(value) <= 32:
            # Embedded value leaf

            # 6-bit - size of value
            encoded_size: Byte = Byte(len(value))
            node[0].set_bits(slice(2, 8), encoded_size.to_bit_array()[2:8])

            # Store key and value 
            node[1:32] = key[:31]  # First 31 bytes for key
            node[32:32+len(value)] = value  # Value bytes
            # Rest is already zeroed
        else:
            # Regular leaf - second bit is 1
            node[0].set_bits(1, 1)

            node[1:32] = key[:31]  # First 31 bytes for key
            node[32:] = self.hash_function(bytes(value))  # Hash of value in last 32 bytes
            
        return node