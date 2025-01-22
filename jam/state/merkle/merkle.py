from typing import Dict, List, Tuple
from jam.types.protocol.crypto import Hash
from jam.types.base.sequences.bytes import ByteArray32, ByteArray64
from jam.state.merkle.trie import MerkleTrie, NodeHash, EncodedNode

class StateMerkle:
    """State Merklization implementation as defined in D.2
    
    This class implements the Mσ function which transforms a serialized state mapping
    into a cryptographic commitment using a binary Merkle Patricia trie.
    """
    
    def __init__(self, hash_function: Hash = Hash.blake2b):
        """Initialize state merkle with optional hash function"""
        self.trie = MerkleTrie(hash_function)

    def _get_bit(self, key: ByteArray32, index: int) -> bool:
        """Get bit at index from key.
        
        Args:
            key: 32-byte array to extract bit from
            index: Position of bit to extract (0-255)
            
        Returns:
            bool: Value of bit at specified index
        """
        byte_index = index >> 3  # Divide by 8
        bit_position = index & 7  # Modulo 8
        return bool(key[byte_index].value[bit_position])

    def _merkelize_recursive(self, items: List[Tuple[ByteArray32, ByteArray32]], bit_index: int) -> Tuple[NodeHash, EncodedNode]:
        """Recursive merkelization"""
        if bit_index >= 256:
            raise ValueError("bit_index exceeds maximum value of 255")
        if not items:
            return (self.trie.node.ZERO_HASH, ByteArray64([0] * 64))
        
        if len(items) == 1:
            key, value = items[0]
            encoded = self.trie.node.encode_leaf(key, value)
            node_hash = NodeHash(self.trie.hash_function(bytes(encoded)))
            self.trie._nodes[node_hash] = encoded
            return (node_hash, encoded)
            
        # Split items by current bit
        left = []
        right = []
        for key, value in items:
            if self._get_bit(key, bit_index):
                right.append((key, value))
            else:
                left.append((key, value))
                
        # Recursively merkelize subtrees
        left_hash, left_encoded = self._merkelize_recursive(left, bit_index + 1)
        right_hash, right_encoded = self._merkelize_recursive(right, bit_index + 1)
        
        # Create branch node
        encoded = self.trie.node.encode_branch(left_hash, right_hash)
        node_hash = NodeHash(self.trie.hash_function(bytes(encoded)))
        self.trie._nodes[node_hash] = encoded
        
        return (node_hash, encoded)

    def merkelize(self, state_dict: Dict[ByteArray32, ByteArray32]) -> NodeHash:
        """Merkelize a state dictionary into a cryptographic commitment (Mσ function)
        
        Args:
            state_dict: Dictionary mapping state keys to their serialized values
            
        Returns:
            bytes: The root hash of the resulting Merkle trie
        """
        # Clear any previous state
        self.clear()
        
        if not state_dict:
            return self.trie.node.ZERO_HASH
            
        # Sort items to ensure deterministic merklization
        items = sorted(state_dict.items())
        
        # Merkelize recursively starting from bit index 0
        root_hash, root_encoded = self._merkelize_recursive(items, 0)
        self.trie._root_hash = root_hash
        return root_hash
    
    def get_nodes(self) -> Dict[NodeHash, EncodedNode]:
        """Get all nodes in the trie, useful for proof generation"""
        return self.trie._nodes.copy()
        
    def clear(self) -> None:
        """Clear the trie state"""
        self.trie._nodes.clear()
        self.trie._root_hash = self.trie.node.ZERO_HASH 