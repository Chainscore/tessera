

from typing import Dict, List, Tuple
from jam.types.base.bit import Bit
from jam.types.protocol.crypto import Hash
from jam.types.base.sequences.bytes import ByteArray32, ByteArray64
from jam.state.merkle.trie import MerkleTrie, NodeHash, EncodedNode


class StateMerkle:
    """State Merklization implementation as defined in D.2.

    This class implements the Mσ function that transforms a serialized state mapping
    into a cryptographic commitment using a binary Merkle Patricia trie.
    
    In this version the tree is built (via _merkelize_recursive) to return a
    full tree structure. Additionally, update_tree_bulk allows multiple key-value
    updates to be applied and the tree recalculated accordingly.
    """

    def __init__(self, hash_function: Hash = Hash.blake2b):
        """Initialize state merkle with an optional hash function."""
        self.trie = MerkleTrie(hash_function)
        print("StateMerkle initialized")

    def bits(self, key: ByteArray32) -> List[Bit]:
        """
        Convert the key into a list of bits from MSB to LSB.
        https://graypaper.fluffylabs.dev/#/68eaa1f/071001071101?v=0.6.4
        """
        bits_list = []
        for octet in key:
            bits_list.extend(octet.value)
        return bits_list

    def _merkelize_recursive(
        self, items: List[Tuple[ByteArray32, ByteArray32]], bit_index: int
    ) -> Tuple[NodeHash, EncodedNode, dict]:
        """
        Recursive merkelization according to the M function (D.2) that builds the tree.
        `M` function as defined in D.2 
        https://graypaper.fluffylabs.dev/#/68eaa1f/39e20039e200?v=0.6.4
        
        Args:
            items: List of tuples containing key-value pairs
            bit_index: Current bit index to split on. We are using bit index instead of slicing bits(key)
            because it's more efficient.
        Returns:
            Tuple containing:
                - node_hash: The hash of the current node
                - encoded_node: The encoded representation of the current node
                - tree_structure: The tree structure of the current node

        The tree structure is represented as a nested dictionary:
          - "leaf" nodes hold key, value, and their encoded representation.
          - "branch" nodes hold the splitting bit index, left/right children, and the encoded branch.
          - "empty" nodes are represented with {"type": "empty"}.
        """
        if bit_index >= 256:
            raise ValueError("bit_index exceeds maximum value of 255")
        
        # If we have no items, return the zero hash and an empty encoded node 
        # https://graypaper.fluffylabs.dev/#/68eaa1f/391c00391d00?v=0.6.4
        if not items:
            empty_encoded = ByteArray64([0] * 64)
            return (self.trie.node.ZERO_HASH, empty_encoded, {"type": "empty"})
        # If we have only one item, we can directly encode it as a leaf node `L`
        # https://graypaper.fluffylabs.dev/#/68eaa1f/396100396100?v=0.6.4
        
        # Also return the leaf node if we have only one item
        if len(items) == 1:
            key, value = items[0]
            encoded_leaf = self.trie.node.encode_leaf(key, value)
            node_hash = NodeHash(self.trie.hash_function(bytes(encoded_leaf)))
            self.trie._nodes[node_hash] = encoded_leaf
            return (
                node_hash, 
                encoded_leaf, 
                {"type": "leaf", "key": key, "value": value, "encoded": encoded_leaf}
            )
        # Split items left/right by current bit
        # https://graypaper.fluffylabs.dev/#/68eaa1f/391701393301?v=0.6.4

        
        left_items = []
        right_items = []
        for key, value in items:
            key_bits = self.bits(key)
            if key_bits[bit_index % len(key_bits)]:
                right_items.append((key, value))
            else:
                left_items.append((key, value))
        # Recursively merkelize subtrees
        left_hash, left_encoded, left_tree = self._merkelize_recursive(left_items, bit_index + 1)
        right_hash, right_encoded, right_tree = self._merkelize_recursive(right_items, bit_index + 1)
        # Create branch node `B` and also return the encoded branch
        encoded_branch = self.trie.node.encode_branch(left_hash, right_hash)
        node_hash = NodeHash(self.trie.hash_function(bytes(encoded_branch)))
        self.trie._nodes[node_hash] = encoded_branch
        
        branch_tree = {
            "type": "branch",
            "bit_index": bit_index,
            "left": left_tree,
            "right": right_tree,
            "encoded": encoded_branch
        }
        return (node_hash, encoded_branch, branch_tree)

    def merkelize(self, state_dict: Dict[ByteArray32, ByteArray32]) -> Tuple[NodeHash, dict]:
        """
        Merkelize a state dictionary into a cryptographic commitment using the Mσ function,
        
        Args:
            state_dict: Dictionary mapping state keys to their serialized values
        Returns:
            Tuple containing:
                - root_hash: The root hash of the merkelized state
                - tree_structure: The tree structure of the merkelized state
        """
        # Clear any previous state
        self.clear()
        if not state_dict:
            return (self.trie.node.ZERO_HASH, {"type": "empty"})

        # Sort items to ensure deterministic merklization
        items = sorted(state_dict.items())
        # Merkelize recursively starting from bit index 0
        root_hash, root_encoded, tree_structure = self._merkelize_recursive(items, 0)
        self.trie._root_hash = root_hash
        return (root_hash, tree_structure)

    def get_nodes(self) -> Dict[NodeHash, EncodedNode]:
        """Return all stored nodes in the trie (useful for proof generation)."""
        return self.trie._nodes.copy()
    
    def clear(self) -> None:
        """Clear the trie state."""
        self.trie._nodes.clear()
        self.trie._root_hash = self.trie.node.ZERO_HASH

    def collect_keys(self, tree: dict, prefix: List[int] = None) -> List[Tuple[List[int], ByteArray32]]:
        """
        Traverse the tree structure and collect all key-value pairs.
        Args:
            tree: The tree structure to traverse
            prefix: The bit path to the current node
        Returns:
            A list of tuples containing:
                - prefix: The bit path to the current node
                - key: The key of the current node
        """
        if prefix is None:
            prefix = []
        result = []
        if tree["type"] == "leaf":
            result.append((prefix, tree["key"]))
        elif tree["type"] == "branch":
            result.extend(self.collect_keys(tree["left"], prefix + [0]))
            result.extend(self.collect_keys(tree["right"], prefix + [1]))
        return result

    def find_in_tree(self, tree: dict, key: ByteArray32, bit_index: int = 0) -> dict:
        """
        Traverse the tree and return the leaf node matching the given key.
        Args:
            tree: The tree structure to traverse
            key: The key to search for
            bit_index: The current bit index to split on
        Returns:
            The leaf node matching the given key or None if not found
        """
        if tree["type"] == "empty":
            return None
        if tree["type"] == "leaf":
            return tree if tree["key"] == key else None
        key_bits = self.bits(key)
        current_bit = key_bits[bit_index % len(key_bits)]
        if current_bit:
            return self.find_in_tree(tree["right"], key, bit_index + 1)
        else:
            return self.find_in_tree(tree["left"], key, bit_index + 1)

    def find_child_hash(self, tree: dict) -> NodeHash:
        """
        Helper to compute the hash from a child node's encoded field.
        Args:
            tree: The tree structure to traverse
        Returns:
            The hash of the child node's encoded field or the zero hash if the encoded field is None
        """
        encoded = tree.get("encoded")
        if encoded is None:
            return self.trie.node.ZERO_HASH
        return NodeHash(self.trie.hash_function(bytes(encoded)))

    def update_tree(self, tree: dict, key: ByteArray32, new_value: ByteArray32, bit_index: int = 0) -> Tuple[NodeHash, dict]:
        """
        Update or insert a key-value pair in the tree.
        Traverses the tree using the key's bits, updates the corresponding leaf (or inserts new leaf if not found),
        and backtracks to update branch encodings and hashes.
        
        Args:
            tree: The tree structure to traverse
            key: The key to update or insert
            new_value: The new value to associate with the key
            bit_index: The current bit index to split on
        Returns:
            A tuple containing:
                - new_node_hash: The hash of the updated or inserted node
                - updated_tree: The updated tree structure
        """
        # print("Kye-->",key,len(self.bits(key)))

        if tree["type"] == "empty":
            # print("Empty-->",key,new_value,self.trie.node.encode_leaf(key, new_value))
            encoded_leaf = self.trie.node.encode_leaf(key, new_value)
            new_hash = NodeHash(self.trie.hash_function(bytes(encoded_leaf)))
            self.trie._nodes[new_hash] = encoded_leaf
            return (new_hash, {"type": "leaf", "key": key, "value": new_value, "encoded": encoded_leaf})
        
        if tree["type"] == "leaf":
            
            if tree["key"] == key:
                encoded_leaf = self.trie.node.encode_leaf(key, new_value)
                new_hash = NodeHash(self.trie.hash_function(bytes(encoded_leaf)))
                self.trie._nodes[new_hash] = encoded_leaf
                return (new_hash, {"type": "leaf", "key": key, "value": new_value, "encoded": encoded_leaf})
            else:
                # Conflict: re-merge this leaf and the new key-value pair.
                existing_item = (tree["key"], tree["value"])
                new_item = (key, new_value)
                # print("merkelize_recursive working...")
                new_hash, new_encoded, new_subtree = self._merkelize_recursive([existing_item, new_item], bit_index)
                return (new_hash, new_subtree)
        key_bits = self.bits(key)
        current_bit = key_bits[bit_index % len(key_bits)]
        if current_bit:
            new_right_hash, updated_right = self.update_tree(tree["right"], key, new_value, bit_index + 1)
            left_hash = self.find_child_hash(tree["left"])
            new_encoded = self.trie.node.encode_branch(left_hash, new_right_hash)
            new_hash = NodeHash(self.trie.hash_function(bytes(new_encoded)))
            self.trie._nodes[new_hash] = new_encoded
            updated_node = {
                "type": "branch",
                "bit_index": tree["bit_index"],
                "left": tree["left"],
                "right": updated_right,
                "encoded": new_encoded
            }
            return (new_hash, updated_node)
        else:
            new_left_hash, updated_left = self.update_tree(tree["left"], key, new_value, bit_index + 1)
            right_hash = self.find_child_hash(tree["right"])
            new_encoded = self.trie.node.encode_branch(new_left_hash, right_hash)
            new_hash = NodeHash(self.trie.hash_function(bytes(new_encoded)))
            self.trie._nodes[new_hash] = new_encoded
            updated_node = {
                "type": "branch",
                "bit_index": tree["bit_index"],
                "left": updated_left,
                "right": tree["right"],
                "encoded": new_encoded
            }
            return (new_hash, updated_node)

    def update_tree_bulk(self, tree: dict, updates: Dict[ByteArray32, ByteArray32]) -> Tuple[NodeHash, dict]:
        """
        Update the tree with multiple key-value pairs.
        Args:
            tree: The tree structure to traverse
            updates: A dictionary mapping keys to their new values
        Returns:
            A tuple containing:
                - new_root_hash: The hash of the updated root node
                - updated_tree: The updated tree structure
        
        """
        current_tree = tree
        # For each key-value update, perform an update of the subtree.
        for key, new_value in updates.items():
            new_hash, current_tree = self.update_tree(current_tree, key, new_value, 0)
        # Optionally, update the global root hash of the trie.
        self.trie._root_hash = new_hash
        return (new_hash, current_tree)
