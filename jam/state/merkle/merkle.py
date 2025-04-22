from typing import Dict, List, Tuple, Optional
from jam.types.base.sequences.bytes import ByteArray32, ByteArray64, Bytes
from jam.state.merkle.trie import MerkleTrie, NodeHash, DBNode
from jam.types.protocol.crypto import Hash
from jam.utils.byte_utils import ByteUtils
from jam.state.merkle.node import Node  # provides node_part()
from jam.db.kv import KVStore

class StateMerkle:
    """
    Implements the canonical state Merklization (per D.2) using a persistent node model.
    https://graypaper.fluffylabs.dev/#/68eaa1f/392f0039af00?v=0.6.4
    
    - Builds a binary Merkle trie in-memory and records two mappings:
      1) _nodes: transient node data (hash -> encoded bytes) for quick in-memory operations.
      2) _db_nodes: DBNode entries with type, metadata, and encoded bytes for path updates.
    - merkelize(): full rebuild from a key->value dict, optionally persisting value blobs via KVStore.
    - find_path(): walks _db_nodes from root to leaf for a given key, returning node-hash path.
    - update_path(): rewrites just the leaf and its branch ancestors in-memory, updating both mappings.
    - update_global_root(): applies multiple leaf updates sequentially, updating the root hash each time.
    """

    def __init__(self, hash_function: Hash = Hash.blake2b):
        # Underlying MerkleTrie holds ZERO_HASH, node encoding helpers, and transient _nodes store.
        self.trie = MerkleTrie(hash_function)

    def bits(self, key: ByteArray32) -> List[int]:
        """
        Expand a 32-byte key into a flat list of 256 bits (0 or 1).
        Expects each octet.value to expose its bits in MSB-first order.
        """
        bits_list: List[int] = []
        for octet in key:
            # Convert each bit in the octet.value sequence to integer 0 or 1
            bits_list.extend([int(bit) for bit in octet.value])
        return bits_list

    def _merkelize_recursive(
        self,
        items: List[Tuple[ByteArray32, ByteArray32]],
        bit_index: int
    ) -> Tuple[NodeHash, ByteArray64]:
        """
        Core recursive routine to build a balanced binary Merkle trie:
        - Splits items along bit_index into left/right subsets.
        - On leaf (single item), emits an encoded leaf node and stores in both _nodes and _db_nodes.
        - On branch, recurses, encodes branch node, and persists metadata in _db_nodes.
        Returns the (hash, encoded_bytes) for the current subtree.
        """
        if bit_index >= 256:
            raise ValueError("bit_index exceeds maximum of 255")

        # Empty subtree => return ZERO_HASH and a 64-byte zero encoding
        if not items:
            empty_encoded = ByteArray64([0] * 64)
            return (self.trie.node.ZERO_HASH, empty_encoded)

        # Single-item subtree => leaf
        if len(items) == 1:
            key, value = items[0]
            encoded_leaf = self.trie.node.encode_leaf(key, value)
            node_hash = NodeHash(self.trie.hash_function(bytes(encoded_leaf)))
            # Transient store for quick lookup
            self.trie._nodes[node_hash] = encoded_leaf
            # Persistent DBNode for path updates later
            leaf_type = self.trie.node.node_part(encoded_leaf)
            self.trie._db_nodes[node_hash] = DBNode(
                node_type=leaf_type,
                encoded=encoded_leaf,
                key=NodeHash(key)
            )
            return (node_hash, encoded_leaf)

        # Partition items by current bit
        left_items, right_items = [], []
        for key, value in items:
            key_bits = self.bits(key)
            if key_bits[bit_index]:
                right_items.append((key, value))
            else:
                left_items.append((key, value))

        # Build subtrees
        left_hash, left_encoded = self._merkelize_recursive(left_items, bit_index + 1)
        right_hash, right_encoded = self._merkelize_recursive(right_items, bit_index + 1)

        # Encode current branch
        encoded_branch = self.trie.node.encode_branch(left_hash, right_hash)
        node_hash = NodeHash(self.trie.hash_function(bytes(encoded_branch)))
        # Store branch in both transient and persistent maps
        self.trie._nodes[node_hash] = encoded_branch
        self.trie._db_nodes[node_hash] = DBNode(
            node_type="branch",
            encoded=encoded_branch,
            bit_index=bit_index,
            left=left_hash,
            right=right_hash
        )
        return (node_hash, encoded_branch)

    def merkelize(
        self,
        state_dict: Dict[ByteArray32, ByteArray32],
        db: Optional[KVStore] = None
    ) -> Tuple[NodeHash, Dict[NodeHash, DBNode]]:
        """
        Implements the state Merklization (per D.2)
        https://graypaper.fluffylabs.dev/#/68eaa1f/39e200393301?v=0.6.4
        
        Fully rebuilds the trie from scratch using the provided key->value map.
        Clears any previous state, invokes the recursive builder, sets _root_hash,
        and optionally persists raw key/value blobs into the given KVStore.
        Returns the new root hash and the persistent node map.
        """
        self.clear()
        if not state_dict:
            return self.trie.node.ZERO_HASH, self.trie._db_nodes
        items = sorted(state_dict.items())
        root_hash, _ = self._merkelize_recursive(items, 0)
        self.trie._root_hash = root_hash
        if db is not None:
            for key, value in state_dict.items():
                db.put(bytes(key), bytes(value))
        return root_hash, self.trie._db_nodes

    def get_nodes(self) -> Dict[NodeHash, DBNode]:
        """
        Return a shallow copy of the persistent DBNode map:
        NodeHash -> DBNode
        """
        return self.trie._db_nodes.copy()

    def clear(self) -> None:
        """
        Reset both transient and persistent node maps and root hash.
        Does not touch any external KVStore.
        """
        self.trie._db_nodes.clear()
        self.trie._nodes.clear()
        self.trie._root_hash = self.trie.node.ZERO_HASH

    def find_path(self, key: ByteArray32) -> List[NodeHash]:
        """
        Walks the persistent DBNode map from current root to the leaf matching 'key'.
        Returns the list of NodeHash along the path, including root and leaf.
        Stops early if ZERO_HASH reached or no child found.
        """
        path: List[NodeHash] = []
        current_hash = self.trie._root_hash
        if current_hash == self.trie.node.ZERO_HASH:
            return path
        path.append(current_hash)
        key_bits = self.bits(key)
        bit_index = 0
        while True:
            node_obj = self.trie._db_nodes.get(current_hash)
            if node_obj is None or node_obj.node_type != "branch":
                return path
            bit = key_bits[bit_index]
            next_hash = node_obj.right if bit else node_obj.left
            if next_hash is None:
                return path
            current_hash = next_hash
            path.append(current_hash)
            bit_index += 1

    def update_path(self, key: ByteArray32, new_value: Bytes) -> NodeHash:
        """
        Update a single leaf value 'new_value' at 'key', then update only
        the branch nodes on its path, rewiring hashes upward to the root.
        Returns the new root hash.
        """
        path = self.find_path(key)
        if not path:
            raise KeyError("Key path not found in trie")
        # Re-encode and hash leaf
        leaf_encoded = self.trie.node.encode_leaf(key, new_value)
        new_leaf_hash = NodeHash(self.trie.hash_function(bytes(leaf_encoded)))
        # Store new leaf
        self.trie._nodes[new_leaf_hash] = leaf_encoded
        self.trie._db_nodes[new_leaf_hash] = DBNode(
            node_type=self.trie.node.node_part(leaf_encoded),
            encoded=leaf_encoded,
            key=NodeHash(key)
        )
        path[-1] = new_leaf_hash
        key_bits = self.bits(key)
        # Recompute branch nodes in reverse path
        for idx in range(len(path) - 2, -1, -1):
            bit_position = self.trie._db_nodes[path[idx]].bit_index
            bit = key_bits[bit_position]
            left_hash = path[idx+1] if not bit else self.trie._db_nodes[path[idx]].left
            right_hash = path[idx+1] if bit else self.trie._db_nodes[path[idx]].right
            new_encoded = self.trie.node.encode_branch(left_hash, right_hash)
            new_parent_hash = NodeHash(self.trie.hash_function(bytes(new_encoded)))
            self.trie._nodes[new_parent_hash] = new_encoded
            self.trie._db_nodes[new_parent_hash] = DBNode(
                node_type="branch",
                encoded=new_encoded,
                bit_index=bit_position,
                left=left_hash,
                right=right_hash
            )
            path[idx] = new_parent_hash
        # Update root
        self.trie._root_hash = path[0]
        return path[0]

    def update_global_root(self, updates: Dict[ByteArray32, Bytes]) -> NodeHash:
        """
        Apply multiple leaf updates sequentially:
        - For each key: re-encode leaf and update its path.
        """
        for key, new_value in updates.items():
            self.update_path(key, new_value)
        return self.trie._root_hash
