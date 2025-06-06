from typing import Dict, List, Tuple, Optional
from jam.state.merkle.node import Node
from jam.state.merkle.utils import ZERO_HASH, NodeHash, NodeType, encode_branch, encode_leaf
from jam.types.protocol.crypto import Hash
from rockstore import RockStore
from tsrkit_types.bytes import Bytes

class StateTrie:
    """
    Implements the canonical state Merklization (per D.2) using a persistent node model.
    https://graypaper.fluffylabs.dev/#/68eaa1f/392f0039af00?v=0.6.4
    
    - Builds a binary Merkle trie in-memory and records mapping nodes: entries with type, metadata, and encoded bytes for path updates.
    - merkelize(): full rebuild from a key->value dict
    - update(): Rewrites the leaf and its branch ancestors in-memory, updating both mappings. Applies path based leaf updates sequentially, updating the root hash each time.
    """
    
    # Dictionary mapping a node hash to Node data (encoded data [ba64], bit_index, left and right node hashes)
    nodes: Dict[Bytes[32], Node]
    # Cache the root
    root_hash: Bytes[32]
    
    def __init__(self):
        self.nodes = {}
        self.root_hash = Bytes[32]([0] * 32)

    def _merkelize_recursive(
        self,
        leaves: List[Bytes[64]],
        bit_index: int
    ) -> Tuple[NodeHash, Bytes[64]]:
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
            return ZERO_HASH, Bytes[64]([0] * 64)

        # Single-item subtree => leaf
        if len(leaves) == 1:
            encoded_leaf = leaves[0]
            node_hash = NodeHash(Hash.blake2b(bytes(encoded_leaf)))
            self.nodes[node_hash] = Node(
                encoded=encoded_leaf,
                bit_index=bit_index
            )
            return node_hash, encoded_leaf

        # Partition items by current bit
        left_items, right_items = [], []
        for leaf in leaves:
            if leaf.to_bits()[8 + bit_index]:
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
            right=right_hash
        )
        return node_hash, encoded_branch

    def merkelize(
        self,
        state_dict: Dict[Bytes, Bytes],
        db: Optional[RockStore] = None
    ) -> Tuple[NodeHash, Dict[NodeHash, Node]]:
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
        if db is not None:
            for key, value in state_dict.items():
                db.put(bytes(key), bytes(value))
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

    def update(self, key: Bytes[32], new_value: Bytes) -> NodeHash:
        """
        Update a single leaf value 'new_value' at 'key', then update only
        the branch nodes on its path, rewiring hashes upward to the root.
        Returns the new root hash.
        """
        self.root_hash = self._recontrust_root(self.root_hash, Node(encoded=encode_leaf(key, new_value)))
        return self.root_hash
    
    def _recontrust_root(self, root: Bytes[32], node: Node, bit_index = 0) -> NodeHash:
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
            if current_node.key_bits_248 == node.key_bits_248:
                nh = NodeHash(Hash.blake2b(node.encoded))
                self.nodes[nh] = node
                self.nodes.pop(root)
                return nh
            # else create a new trie from here, and attach it
            return self._merkelize_recursive([current_node.encoded, node.encoded], bit_index=bit_index)[0]
        # Branch [update]
        else:
            # if 0, go left
            if node.key_bits_248[bit_index] == 0:
                current_node.left = self._recontrust_root(current_node.left, node, bit_index=bit_index+1)
            else:
                current_node.right = self._recontrust_root(current_node.right, node, bit_index=bit_index+1)
            
            new_encoded = encode_branch(current_node.left or ZERO_HASH, current_node.right or ZERO_HASH)
            new_parent_hash = NodeHash(Hash.blake2b(bytes(new_encoded)))
            
            self.nodes[new_parent_hash] = Node(
                encoded=new_encoded,
                bit_index=bit_index,
                left=current_node.left,
                right=current_node.right
            )
            
            return new_parent_hash

    def delete(self, key: Bytes[32]) -> NodeHash:
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
        new_root, removed = self._delete_recursive(
            self.root_hash,
            key_bits,
            bit_index=0
        )

        # If nothing was removed we keep the existing root hash.
        self.root_hash = new_root if removed else self.root_hash
        return self.root_hash

    def _delete_recursive(
            self,
            subtree_hash: Bytes[32],
            key_bits: List[int],
            bit_index: int
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
            new_right_hash, removed = self._delete_recursive(
                node.right, key_bits, bit_index + 1
            )
            new_left_hash = node.left
        else:
            new_left_hash, removed = self._delete_recursive(
                node.left, key_bits, bit_index + 1
            )
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
    def _is_leaf(self, h: Bytes[32]) -> bool:
        if h == ZERO_HASH:
            return False
        n = self.nodes.get(h)
        return n is not None and n.type is not NodeType.BRANCH

    def __repr__(self):
        return f"StateTrie(root={self.root_hash}, nodes={self.nodes})"