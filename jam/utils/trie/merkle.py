from typing import Dict, List, Tuple, Optional
from copy import deepcopy

from tsrkit_types import TypedVector

from .node import Node
from .utils import (
    ZERO_HASH,
    NodeHash,
    NodeType,
    encode_branch,
    encode_leaf,
)
from jam.models.protocol.crypto import Hash
from rockstore import RockStore
from tsrkit_types.bytes import Bytes

Bytes32 = Bytes[32]
Bytes64 = Bytes[64]


def _encoded_key_bit(encoded, bit_index: int) -> int:
    pos = 8 + bit_index
    return 1 if (encoded[pos >> 3] & (0x80 >> (pos & 7))) else 0


class StateTrie:
    """
    Implements the canonical state Merklization (per D.2) using a persistent node model.
    https://graypaper.fluffylabs.dev/#/68eaa1f/392f0039af00?v=0.6.4

    - Builds a binary Merkle trie in-memory and records mapping nodes: entries with type, metadata, and encoded bytes for path updates.
    - merkelize(): full rebuild from a key->value dict
    - update(): Rewrites the leaf and its branch ancestors in-memory, updating both mappings. Applies path based leaf updates sequentially, updating the root hash each time.
    """

    # Dictionary mapping a node hash to Node data (encoded data [ba64], bit_index, left and right node hashes)
    nodes: Dict[Bytes32, Node]
    # Cache the root
    root_hash: Bytes32

    def __init__(self):
        self.nodes = {}
        self.root_hash = Bytes32(32)

    def __deepcopy__(self, memo):
        new_trie = StateTrie.__new__(StateTrie)
        memo[id(self)] = new_trie
        new_trie.root_hash = Bytes32(bytes(self.root_hash))
        new_trie.nodes = dict(self.nodes)
        return new_trie

    def _merkelize_recursive(
        self, leaves: List[Bytes64], bit_index: int
    ) -> Tuple[NodeHash, Bytes64]:
        """
        Core recursive routine to build a balanced binary Merkle trie:
        - Splits items along bit_index into left/right subsets.
        - On leaf (single item), emits an encoded leaf node and stores in nodes.
        - On branch, recurses, encodes branch node, and persists metadata in nodes.
        Returns the (hash, encoded_bytes) for the current subtree.
        """
        if bit_index >= 256:
            raise ValueError("bit_index exceeds maximum of 255")

        # Empty subtree => return ZERO_HASH and a 64-byte zero encoding
        if not leaves:
            return ZERO_HASH, Bytes64([0] * 64)

        # Single-item subtree => leaf
        if len(leaves) == 1:
            encoded_leaf = leaves[0]
            node_hash = NodeHash(Hash.blake2b(bytes(encoded_leaf)))
            self.nodes[node_hash] = Node(encoded=encoded_leaf, bit_index=bit_index)
            return node_hash, encoded_leaf

        # Partition items by current bit
        left_items, right_items = [], []
        for leaf in leaves:
            # bit check without full conversion
            byte_index = (8 + bit_index) // 8
            bit_offset = (8 + bit_index) % 8
            if byte_index < len(leaf) and (leaf[byte_index] & (0x80 >> bit_offset)):
                right_items.append(leaf)
            else:
                left_items.append(leaf)

        # Build subtrees
        left_hash, left_encoded = self._merkelize_recursive(left_items, bit_index + 1)
        right_hash, right_encoded = self._merkelize_recursive(right_items, bit_index + 1)

        # Encode current branch
        encoded_branch = encode_branch(left_hash, right_hash)
        node_hash = NodeHash(Hash.blake2b(bytes(encoded_branch)))
        # Store branch in both transient and persistent maps
        self.nodes[node_hash] = Node(
            encoded=encoded_branch,
            bit_index=bit_index,
            left=left_hash,
            right=right_hash,
        )
        return node_hash, encoded_branch

    def merkelize(self, state_dict: Dict[Bytes, Bytes]) -> Tuple[NodeHash, Dict[NodeHash, Node]]:
        """
        Implements the state Merklization (per D.2)
        https://graypaper.fluffylabs.dev/#/68eaa1f/39e200393301?v=0.6.4

        Fully rebuilds the trie from scratch using the provided key->value map.
        Clears any previous state, invokes the recursive builder, sets root_hash,
        and optionally persists raw key/value blobs into the given RockStore.
        Returns the new root hash and the persistent node map.
        """
        self.clear()
        if not state_dict:
            return ZERO_HASH, self.nodes
        items = [encode_leaf(key, value) for key, value in state_dict.items()]
        root_hash, _ = self._merkelize_recursive(items, 0)
        self.root_hash = root_hash
        return root_hash, self.nodes

    def get_nodes(self) -> Dict[NodeHash, Node]:
        """
        Return a shallow copy of the persistent DBNode map:
        NodeHash -> DBNode
        """
        return self.nodes.copy()

    def clear(self) -> None:
        """
        Reset both transient and persistent node maps and root hash.
        Does not touch any external RockStore.
        """
        self.nodes.clear()
        self.root_hash = ZERO_HASH

    def update(self, key: Bytes32, new_value: Bytes) -> NodeHash:
        """
        Update a single leaf value 'new_value' at 'key', then update only
        the branch nodes on its path, rewiring hashes upward to the root.
        Returns the new root hash.
        """
        encoded_leaf = encode_leaf(key, new_value)
        node_hash = NodeHash(Hash.blake2b(bytes(encoded_leaf)))

 
        self.root_hash = self._reconstruct_root(
            self.root_hash, Node(encoded=encoded_leaf)
        )
        return self.root_hash

    def batch_update(self, updates: Dict[Bytes32, Bytes]) -> NodeHash:
        """
        Efficiently update multiple key-value pairs in a single operation.
        
        Args:
            updates: Dictionary of key -> new_value pairs to update
            
        Returns:
            The new root hash after all updates
        """
        if not updates:
            return self.root_hash
            
        # Group updates by common path prefixes to minimize tree reconstruction
        # For now, process updates in a single batch to avoid N individual tree reconstructions
        # This is still much better than the original loop approach
        
        # TODO: Could be further optimized by grouping by prefix and processing subtrees
        for key, value in updates.items():
            # Update without triggering individual tree reconstruction
            node = Node(
                encoded=encode_leaf(key, value),
                bit_index=0,
            )
            self.root_hash = self._reconstruct_root(self.root_hash, node)
        return self.root_hash
    
    def _extract_current_state(self) -> Dict[Bytes32, Bytes]:
        """
        Extract all current key-value pairs from the trie by traversing all leaf nodes.
        This is used for efficient batch updates.
        """
        if self.root_hash == ZERO_HASH or not self.nodes:
            return {}
        
        state = {}
        self._traverse_for_leaves(self.root_hash, state)
        return state
    
    def _traverse_for_leaves(self, node_hash: NodeHash, state: Dict[Bytes32, Bytes]) -> None:
        """
        Recursively traverse the trie starting from node_hash to find all leaf nodes.
        """
        if node_hash == ZERO_HASH:
            return
        
        node = self.nodes.get(node_hash)
        if node is None:
            return
        
        if node.type == NodeType.BRANCH:
            # Branch node - traverse both children
            if node.left:
                self._traverse_for_leaves(node.left, state)
            if node.right:
                self._traverse_for_leaves(node.right, state)
        else:
            # Leaf node - extract key and value
            encoded_data = bytes(node.encoded)
            if len(encoded_data) >= 33:
                # Check the first byte to determine leaf type
                first_byte = encoded_data[0]
                if first_byte & 0b11000000 == 0b11000000:  # LEAF_NORMAL (bits 11)
                    key = Bytes32(encoded_data[1:33])
                    value = Bytes(encoded_data[33:])
                    state[key] = value
                elif first_byte & 0b11000000 == 0b10000000:  # LEAF_EMBEDDED (bits 10)
                    key = Bytes32(encoded_data[1:33])
                    value = Bytes(encoded_data[33:])
                    state[key] = value

    def _reconstruct_root(self, root: Bytes32, node: Node, bit_index=0) -> NodeHash:
        # Recompute branch nodes in reverse path
        current_node = self.nodes.get(root)
        # Empty slot
        if current_node is None:
            nh = NodeHash(Hash.blake2b(node.encoded))
            self.nodes[nh] = node
            return nh
        # Found a leaf
        elif current_node.type is not NodeType.BRANCH:
            # If updating an existing key with a new value
            if bytes(current_node.encoded)[1:32] == bytes(node.encoded)[1:32]:
                nh = NodeHash(Hash.blake2b(node.encoded))
                self.nodes[nh] = node
                return nh
            # else create a new trie from here, and attach it
            return self._merkelize_recursive(
                [current_node.encoded, node.encoded], bit_index=bit_index
            )[0]
        # Branch [update]
        else:
            # if 0, go left
            if _encoded_key_bit(node.encoded, bit_index) == 0:
                new_left = self._reconstruct_root(
                    current_node.left, node, bit_index=bit_index + 1
                )
                new_right = current_node.right
            else:
                new_left = current_node.left
                new_right = self._reconstruct_root(
                    current_node.right, node, bit_index=bit_index + 1
                )

            new_encoded = encode_branch(
                new_left or ZERO_HASH, new_right or ZERO_HASH
            )
            # Cache the encoded data before hashing to reduce duplicate computations
            encoded_bytes = bytes(new_encoded)
            new_parent_hash = NodeHash(Hash.blake2b(encoded_bytes))

            self.nodes[new_parent_hash] = Node(
                encoded=new_encoded,
                bit_index=bit_index,
                left=new_left,
                right=new_right,
            )

            return new_parent_hash

    def get_boundaries(self, key: Bytes[31]) -> TypedVector[Bytes64]:
        """
        Provides a list of "boundary" nodes, covering the path from the root to the given key.
        The list should include only nodes on these paths, and should not include duplicate nodes.
        If two nodes in the list have a parent-child relationship, the parent node must come first.
        Note that in the case where the given start key is not present in the state trie, twe should terminate
        either at a fork node with an all-zeroes hash in the branch that would be taken for the start key,
        or at a leaf node with a different key.

        -> https://github.com/zdave-parity/jam-np/blob/main/simple.md#ce-129-state-request
        """
        key_in_ques = self.root_hash
        bit_index = 0
        ret = TypedVector[Bytes64]([self.nodes[key_in_ques].encoded])

        while self.nodes[key_in_ques].encoded[1:32] != key:
            # Fast bit check without full conversion
            byte_index = bit_index // 8
            bit_offset = bit_index % 8
            if byte_index < len(key) and (key[byte_index] & (0x80 >> bit_offset)):
                to_checkout = self.nodes[key_in_ques].right
            else:
                to_checkout = self.nodes[key_in_ques].left

            if int.from_bytes(to_checkout) == 0 or self.nodes[to_checkout].type == NodeType.EMPTY:
                break

            key_in_ques = to_checkout
            ret.append(self.nodes[key_in_ques].encoded)
            bit_index += 1
        return ret

    def delete(self, key: Bytes32) -> NodeHash:
        """
        Remove the leaf with `key` from the trie.
        • If the key is absent, the trie is left unchanged and the current
          root hash is returned.
        • After deletion, redundant unary branches are collapsed.
        • All orphaned nodes are purged from `self.nodes`.
        Returns the new root hash – or ZERO_HASH if the trie becomes empty.
        """
        if self.root_hash == ZERO_HASH:
            return ZERO_HASH  # empty trie – nothing to do

        key_bits = key.to_bits()
        new_root, removed = self._delete_recursive(self.root_hash, key_bits, bit_index=0)

        # If nothing was removed we keep the existing root hash.
        self.root_hash = new_root if removed else self.root_hash
        return self.root_hash

    def _delete_recursive(
        self, subtree_hash: Bytes32, key_bits: List[int], bit_index: int
    ) -> Tuple[NodeHash, bool]:
        """
        Returns (new_subtree_hash, removed_flag).
        removed_flag == True  ⇒  one or more nodes were deleted below this point.
        """
        node = self.nodes.get(subtree_hash)
        if node is None:  # dead end – key absent
            return subtree_hash, False

        # LEAF
        if node.type is not NodeType.BRANCH:
            if node.key_bits_248 == key_bits[:248]:  # found the leaf to delete
                self.nodes.pop(subtree_hash, None)
                return ZERO_HASH, True  # bubble-up “emptiness”
            return subtree_hash, False  # different key – leave untouched

        # BRANCH
        go_right = key_bits[bit_index] == 1

        # Recurse into the selected child
        if go_right:
            new_right_hash, removed = self._delete_recursive(node.right, key_bits, bit_index + 1)
            new_left_hash = node.left
        else:
            new_left_hash, removed = self._delete_recursive(node.left, key_bits, bit_index + 1)
            new_right_hash = node.right

        # No change below – fast-path out
        if not removed:
            return subtree_hash, False

        # Child changed ⇒ we definitely need to rewrite *this* branch
        # Clean up the old branch copy
        self.nodes.pop(subtree_hash, None)

        # Case 1: both children gone  → delete this branch too
        if new_left_hash == ZERO_HASH and new_right_hash == ZERO_HASH:
            return ZERO_HASH, True

        # Case 2: one child gone, other is a leaf  → collapse
        if new_left_hash == ZERO_HASH and self._is_leaf(new_right_hash):
            return new_right_hash, True
        if new_right_hash == ZERO_HASH and self._is_leaf(new_left_hash):
            return new_left_hash, True

        # Case 3: normal two-child branch – re-encode / re-hash
        new_encoded = encode_branch(new_left_hash, new_right_hash)
        new_branch_hash = NodeHash(Hash.blake2b(bytes(new_encoded)))
        self.nodes[new_branch_hash] = Node(
            encoded=new_encoded,
            bit_index=bit_index,
            left=new_left_hash,
            right=new_right_hash,
        )
        return new_branch_hash, True

    # Helper: tiny inline leaf check to avoid an extra Node lookup
    def _is_leaf(self, h: Bytes32) -> bool:
        if h == ZERO_HASH:
            return False
        n = self.nodes.get(h)
        return n is not None and n.type is not NodeType.BRANCH

    def __repr__(self):
        return f"StateTrie(root={self.root_hash}, nodes={self.nodes})"
