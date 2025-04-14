from typing import Dict, List, Tuple, Optional, Literal
from dataclasses import dataclass

from jam.types.base.sequences.bytes import ByteArray32, ByteArray64, Bytes
from jam.state.merkle.trie import MerkleTrie, NodeHash, EncodedNode
from jam.types.protocol.crypto import Hash
from jam.utils.byte_utils import ByteUtils
from jam.state.merkle.node import Node  # provides node_part()
from jam.db.kv import KVStore

# Persistent node type for storing in the database.
DBNodeType = Literal["branch", "leaf_embedded", "leaf_normal", "empty"]

@dataclass
class DBNode:
    node_type: DBNodeType            # "branch", "leaf_embedded", "leaf_normal", "empty"
    encoded: ByteArray64             # the full 64-byte encoded value of the node
    key: Optional[ByteArray32] = None  # For leaf nodes: store only the key (value is externally stored)
    bit_index: Optional[int] = None    # For branch nodes: index used to decide the split
    left: Optional[NodeHash] = None    # For branch nodes: hash pointer to left child
    right: Optional[NodeHash] = None   # For branch nodes: hash pointer to right child

class StateMerkle:
    """State Merklization implementation as defined in D.2 using a persistent node model.
    
    This version constructs the trie and stores a mapping from NodeHash to DBNode objects.
    Later, when a key’s leaf value changes externally, update_path() is used to update only the
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
            self._db_nodes[node_hash] = DBNode(
                node_type=leaf_type,
                encoded=encoded_leaf,
                key=key
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
        node_hash = NodeHash(self.trie.hash_function(bytes(encoded_branch)))
        self.trie._nodes[node_hash] = encoded_branch
        self._db_nodes[node_hash] = DBNode(
            node_type="branch",
            encoded=encoded_branch,
            bit_index=bit_index,
            left=left_hash,
            right=right_hash
        )
        return (node_hash, encoded_branch)

    def merkelize(self, state_dict: Dict[ByteArray32, ByteArray32],db: KVStore=None) -> Tuple[NodeHash,Dict[NodeHash,DBNode]]:
        """
        Build the trie from a state dictionary and return (root_hash, db_nodes).
        """
        self.clear()
        self._db_nodes: Dict[NodeHash, DBNode] = {}
        if not state_dict:
            return self.trie.node.ZERO_HASH,self._db_nodes

        if not state_dict:
            return self.trie.node.ZERO_HASH

        items = sorted(state_dict.items())
        root_hash,_= self._merkelize_recursive(items, 0)
        self.trie._root_hash = root_hash
        return root_hash,self.trie._nodes
    
    def get_nodes(self) -> Dict[NodeHash, DBNode]:
        return self.trie._nodes.copy()
    
    
    
    def clear(self) -> None:
        self.trie._nodes.clear()
        self.trie._root_hash = self.trie.node.ZERO_HASH
        if hasattr(self, "_db_nodes"):
            self._db_nodes.clear()
        if hasattr(self, "_db_nodes"):
            self._db_nodes.clear()

    def find_path(self, key: ByteArray32) -> List[NodeHash]:
        """
        Traverse the DB nodes (from _db_nodes) and return the list of node hashes
        along the path from the root to the leaf corresponding to the key.
        """
        path: List[NodeHash] = []
        current_hash = self.trie._root_hash
        key_bits = self.bits(key)
        bit_index = 0
        while True:
            if current_hash not in self._db_nodes:
                break
            node_obj = self._db_nodes[current_hash]
            path.append(current_hash)
            if node_obj.node_type == "branch":
                # Decide which way to go according to the current bit.
                if key_bits[bit_index % len(key_bits)]:
                    if node_obj.right is None:
                        break
                    current_hash = node_obj.right
                else:
                    if node_obj.left is None:
                        break
                    current_hash = node_obj.left
                bit_index += 1
            else:
                # It's a leaf (or empty); we've reached the end.
                break
        return path

    def update_path(self, key: ByteArray32, new_value: Bytes) -> NodeHash:
        """
        Update the path from the root to the leaf corresponding to the key.
        1. Find the path as a list of node hashes.
        2. Recompute the leaf encoding (using encode_leaf) for the given key and new_value.
        3. Update each branch node along the path by re-encoding the branch (using left/right pointers)
           with the updated child hash.
        
        Returns the new root hash.
        """
        path = self.find_path(key)
        if not path:
            raise ValueError("Key not found in the tree path")
        
        # Update the leaf node.
        leaf_hash = path[-1]
        # Assume that you have a means to fetch the original key-value pair.
        # Here, for update, we re-encode the leaf using the new_value.
        # (Remember: we only store the key in the persistent leaf node.)
        leaf_encoded = self.trie.node.encode_leaf(key, new_value)
        new_leaf_hash = NodeHash(self.trie.hash_function(bytes(leaf_encoded)))
        self.trie._nodes[new_leaf_hash] = leaf_encoded
        # Update persistent DB node for leaf.
        leaf_node = self._db_nodes[leaf_hash]
        leaf_type = self.trie.node.node_part(leaf_encoded)
        self._db_nodes[new_leaf_hash] = DBNode(
            node_type=leaf_type,
            encoded=leaf_encoded,
            key=key
        )
        # Replace leaf in the path.
        path[-1] = new_leaf_hash

        # Now propagate the updated hash upward.
        for i in range(len(path) - 2, -1, -1):
            parent_hash = path[i]
            parent_node = self._db_nodes[parent_hash]
            bit_index = parent_node.bit_index
            # Determine which child was updated.
            if self.bits(key)[bit_index % len(self.bits(key))] == 1:
                updated_child = path[i+1]
                left_child = parent_node.left  # remains unchanged
                new_encoded = self.trie.node.encode_branch(left_child, updated_child)
            else:
                updated_child = path[i+1]
                right_child = parent_node.right  # remains unchanged
                new_encoded = self.trie.node.encode_branch(updated_child, right_child)
            new_parent_hash = NodeHash(self.trie.hash_function(bytes(new_encoded)))
            self.trie._nodes[new_parent_hash] = new_encoded
            # Update the DB node.
            if parent_node.node_type == "branch":
                if self.bits(key)[bit_index % len(self.bits(key))] == 1:
                    self._db_nodes[new_parent_hash] = DBNode(
                        node_type="branch",
                        encoded=new_encoded,
                        bit_index=bit_index,
                        left=parent_node.left,
                        right=updated_child
                    )
                else:
                    self._db_nodes[new_parent_hash] = DBNode(
                        node_type="branch",
                        encoded=new_encoded,
                        bit_index=bit_index,
                        left=updated_child,
                        right=parent_node.right
                    )
            path[i] = new_parent_hash  # update the parent's hash in the path
        
        # The first element in path is now the updated root hash.
        new_root_hash = path[0]
        self.trie._root_hash = new_root_hash
        return new_root_hash

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
            new_root = self.update_path(key, new_value)
        return new_root
