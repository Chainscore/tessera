from typing import Dict, List, Tuple, Optional, Literal
from dataclasses import dataclass

from jam.types.base.sequences.bytes import ByteArray32, ByteArray64, Bytes
from jam.state.merkle.trie import MerkleTrie, NodeHash, EncodedNode, DBNode
from jam.types.protocol.crypto import Hash
from jam.utils.byte_utils import ByteUtils
from jam.state.merkle.node import Node  # provides node_part()
from jam.db.kv import KVStore
from jam.state.merkle.trie import DBNode

class StateMerkle:
    """State Merklization implementation as defined in D.2 using a persistent node model.
    
    This version constructs the trie and stores a mapping from NodeHash to DBNode objects.
    Later, when a key's leaf value changes externally, update_path() is used to update only the
    branch nodes along the path from that leaf up to the root—thereby updating the state root.
    """

    def __init__(self, hash_function: Hash = Hash.blake2b):
        self.trie = MerkleTrie(hash_function)
    def bits(self, key: ByteArray32) -> List[int]:
        """Convert a key to a list of bits (0 or 1)."""
        bits_list = []
        for octet in key:
            # Assume each octet.value is a list of Bits that are convertible to int 0/1.
            bits_list.extend([int(bit) for bit in octet.value])
        return bits_list
    
    def _merkelize_recursive(
        self, items: List[Tuple[ByteArray32, ByteArray32]], bit_index: int
    ) -> Tuple[NodeHash, ByteArray64]:
        """
        Recursive merkelization based on D.2.
        
        Returns a tuple (node_hash, encoded_node). Also populates a persistent _db_nodes dict.
        """
        if bit_index >= 256:
            raise ValueError("bit_index exceeds maximum value of 255")
        
        if not items:
            empty_encoded = ByteArray64([0] * 64)
            return (self.trie.node.ZERO_HASH, empty_encoded)
        
        if len(items) == 1:
            key, value = items[0]
            encoded_leaf = self.trie.node.encode_leaf(key, value)
            node_hash = NodeHash(self.trie.hash_function(bytes(encoded_leaf)))
            self.trie._nodes[node_hash] = encoded_leaf
            leaf_type = self.trie.node.node_part(encoded_leaf)
            
            # Persist leaf node (only store key; value stored elsewhere in DB)
            
            self.trie._db_nodes[node_hash] = DBNode(
                node_type=leaf_type,
                encoded=encoded_leaf,
                key=NodeHash(key)
            )
            return (node_hash, encoded_leaf)
        
        left_items = []
        right_items = []
        for key, value in items:
            key_bits = self.bits(key)
            if key_bits[bit_index % len(key_bits)]:
                right_items.append((key, value))
            else:
                left_items.append((key, value))
        
        left_hash, left_encoded = self._merkelize_recursive(left_items, bit_index + 1)
        right_hash, right_encoded = self._merkelize_recursive(right_items, bit_index + 1)
        
        encoded_branch = self.trie.node.encode_branch(left_hash, right_hash)
        node_hash = NodeHash(self.trie.hash_function(encoded_branch))
      
        self.trie._nodes[node_hash] = encoded_branch
       
        self.trie._db_nodes[node_hash] = DBNode(
            node_type="branch",
            encoded=encoded_branch,
            bit_index=bit_index,
            left=NodeHash(left_hash),
            right=NodeHash(right_hash)
        )
        return (node_hash, encoded_branch)

    def merkelize(self, state_dict: Dict[ByteArray32, ByteArray32], db: KVStore = None) -> Tuple[NodeHash, Dict[NodeHash, DBNode]]:
        """Build the trie in RAM and optionally persist state key-value pairs"""
        self.clear()
        
        if not state_dict:
            return self.trie.node.ZERO_HASH, self.trie._db_nodes

        # Build tree structure in RAM
        items = sorted(state_dict.items())
        root_hash, _ = self._merkelize_recursive(items, 0)
        self.trie._root_hash = root_hash
       
        # Only persist state key-value pairs if db provided
        if db is not None:
            for key, value in state_dict.items():
                db.put(bytes(key), bytes(value))
        
        return root_hash, self.trie._db_nodes
    
    def get_nodes(self) -> Dict[NodeHash, DBNode]:
        return self.trie._nodes.copy()
    
    
    
    def clear(self) -> None:
        self.trie._db_nodes.clear()
        self.trie._nodes.clear()
        self.trie._root_hash = self.trie.node.ZERO_HASH
        

    def find_path(self, key: ByteArray32) -> List[NodeHash]:
        """
        Traverse the DB nodes (from _db_nodes) and return the list of node hashes
        along the path from the root to the leaf corresponding to the key.
        """
        path: List[NodeHash] = []
        current_hash = self.trie._root_hash
        key_bits = self.bits(key)
        bit_index = 0
        
        
        # Add root hash to path
        if current_hash == self.trie.node.ZERO_HASH:
            return path
        
        path.append(current_hash)
        
            
        while True:
            if current_hash==NodeHash([0] * 32):
                return path
            node_obj = self.trie._db_nodes[current_hash]
            if node_obj is None:
                return path
            if node_obj.node_type == "branch":
                # Decide which way to go according to the current bit
                if key_bits[bit_index % len(key_bits)]:
                    if node_obj.right is None:
                        return path
                    current_hash = NodeHash(node_obj.right)
                    path.append(current_hash)
                else:
                    if node_obj.left is None:
                        return path
                    current_hash = NodeHash(node_obj.left)
                    path.append(current_hash)
                bit_index += 1
            else:
                # It's a leaf (or empty); we've reached the end
                return path
    def update_path(self, key: ByteArray32, new_value: Bytes) -> NodeHash:
        """Update path in RAM and optionally persist state update"""
        # Find path using in-memory nodes
        path = self.find_path(key)
 
        if not path:
            raise ValueError("Key not found in the tree path")
        
        # Update leaf node in RAM
        leaf_hash = path[-1]
        leaf_encoded = self.trie.node.encode_leaf(key, new_value)
        new_leaf_hash = NodeHash(self.trie.hash_function(bytes(leaf_encoded)))
        
        # Update RAM structures
        self.trie._nodes[new_leaf_hash] = leaf_encoded
        self.trie._db_nodes[new_leaf_hash] = DBNode(
            node_type=self.trie.node.node_part(leaf_encoded),
            encoded=leaf_encoded,
            key=key
        )
        # TODO: Need to prune the old leaf node
        
        # # Update branch nodes in RAM
        new_root_hash = self._update_branch_nodes(path, key, new_leaf_hash)
        
        return self.trie._root_hash

    def _update_branch_nodes(self, path: List[NodeHash], key: ByteArray32, new_leaf_hash: NodeHash) -> NodeHash:
        """Helper method to update branch nodes in RAM after leaf update"""
        path[-1] = new_leaf_hash
        
        for i in range(len(path) - 2, -1, -1):
            parent_hash = path[i]
            parent_node = self.trie._db_nodes[parent_hash]
            bit_index = parent_node.bit_index
            
            if self.bits(key)[bit_index % len(self.bits(key))] == 1:
                new_encoded = self.trie.node.encode_branch(parent_node.left, path[i+1])
            else:
                new_encoded = self.trie.node.encode_branch(path[i+1], parent_node.right)
            
            new_parent_hash = NodeHash(self.trie.hash_function(bytes(new_encoded)))
            
            # Update RAM structures
            self.trie._nodes[new_parent_hash] = new_encoded
            self.trie._db_nodes[new_parent_hash] = DBNode(
                node_type="branch",
                encoded=new_encoded,
                bit_index=bit_index,
                left=path[i+1] if self.bits(key)[bit_index % len(self.bits(key))] == 0 else parent_node.left,
                right=path[i+1] if self.bits(key)[bit_index % len(self.bits(key))] == 1 else parent_node.right
            )
            path[i] = new_parent_hash
        
        self.trie._root_hash = path[0]
        return path[0]

    def update_global_root(self, updates: Dict[ByteArray32, Bytes]) -> NodeHash:
        """
        Given a set of key:new_value updates (for leaves), update the trie along each key's path
        and then re-calculate the global state root.
        
        This function fetches the current persistent nodes (from _db_nodes),
        iterates over the update dictionary, calls update_path() for each, and finally
        returns the updated root hash.
        """
        new_root = self.trie._root_hash
        
        for key, new_value in updates.items():
            new_root=self.update_path(key, new_value)
        return self.trie._root_hash
