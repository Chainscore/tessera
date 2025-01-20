from typing import Dict, List, Tuple

from jam.types.protocol.crypto import Hash
from jam.types.base.sequences.bytes import ByteArray32
from jam.state.merkle.trie import MerkleTrie, NodeHash, EncodedNode

class StateMerkle:
    """State Merklization implementation as defined in D.2
    
    This class implements the Mσ function which transforms a serialized state mapping
    into a cryptographic commitment using a binary Merkle Patricia trie.
    """
    
    def __init__(self, hash_function: Hash = Hash.blake2b):
        """Initialize state merkle with optional hash function"""
        self.trie = MerkleTrie(hash_function)
    
    def _create_leaf_layer(self, items: List[Tuple[ByteArray32, ByteArray32]]) -> List[Tuple[NodeHash, EncodedNode]]:
        """Create leaf nodes for all items"""
        leaves = []
        for key, value in items:
            encoded = self.trie.node.encode_leaf(key, value)
            node_hash = self.trie.hash_function(bytes(encoded))
            leaves.append((node_hash, encoded))
            self.trie._nodes[node_hash] = encoded
        return leaves
    
    def _create_branch_layer(self, nodes: List[Tuple[NodeHash, EncodedNode]]) -> List[Tuple[NodeHash, EncodedNode]]:
        """Create a layer of branch nodes from pairs of child nodes"""
        branches = []
        for i in range(0, len(nodes), 2):
            # If odd number of nodes, promote last node to next layer
            if i + 1 >= len(nodes):
                branches.append(nodes[i])
                continue
                
            # Create branch node from pair
            left_hash, _ = nodes[i]
            right_hash, _ = nodes[i + 1]
            encoded = self.trie.node.encode_branch(left_hash, right_hash)
            node_hash = self.trie.hash_function(bytes(encoded))
            branches.append((node_hash, encoded))
            self.trie._nodes[node_hash] = encoded
            
        return branches
        
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
        
        # Create leaf nodes
        current_layer = self._create_leaf_layer(items)
        
        # Create branch layers until we reach the root
        while len(current_layer) > 1:
            current_layer = self._create_branch_layer(current_layer)
            
        # Set root hash
        root_hash, root_node = current_layer[0]
        self.trie._root_hash = root_hash
        return root_hash
    
    def get_nodes(self) -> Dict[NodeHash, EncodedNode]:
        """Get all nodes in the trie, useful for proof generation"""
        return self.trie._nodes.copy()
        
    def clear(self) -> None:
        """Clear the trie state"""
        self.trie._nodes.clear()
        self.trie._root_hash = self.trie.node.ZERO_HASH 