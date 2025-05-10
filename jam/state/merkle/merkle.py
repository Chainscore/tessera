from typing import Dict, List, Tuple, Optional
from jam.state.merkle.node import Node
from jam.state.merkle.utils import ZERO_HASH, NodeHash, NodeType, encode_branch, encode_leaf
from jam.types.base.sequences.bytes import ByteArray32, ByteArray64, Bytes
from jam.types.protocol.crypto import Hash
from jam.storage.db.kv import KVStore

class StateTrie:
    """
    Implements the canonical state Merklization (per D.2) using a persistent node model.
    https://graypaper.fluffylabs.dev/#/68eaa1f/392f0039af00?v=0.6.4
    
    - Builds a binary Merkle trie in-memory and records mapping nodes: entries with type, metadata, and encoded bytes for path updates.
    - merkelize(): full rebuild from a key->value dict
    - update(): Rewrites the leaf and its branch ancestors in-memory, updating both mappings. Applies path based leaf updates sequentially, updating the root hash each time.
    """
    
    # Dictionary mapping a node hash to Node data (encoded data [ba64], bit_index, left and right node hashes)
    nodes: Dict[ByteArray32, Node]
    # Cache the root
    root_hash: ByteArray32
    
    def __init__(self):
        self.nodes = {}
        self.root_hash = ByteArray32([0] * 32)

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
        leaves: List[ByteArray64],
        bit_index: int
    ) -> Tuple[NodeHash, ByteArray64]:
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
            return (ZERO_HASH, ByteArray64([0] * 64))

        # Single-item subtree => leaf
        if len(leaves) == 1:
            encoded_leaf = leaves[0]
            node_hash = NodeHash(Hash.blake2b(bytes(encoded_leaf)))
            # Transient store for quick lookup
            # Persistent DBNode for path updates later
            self.nodes[node_hash] = Node(
                encoded=encoded_leaf,
                bit_index=bit_index
            )
            return (node_hash, encoded_leaf)

        # Partition items by current bit
        left_items, right_items = [], []
        for leaf in leaves:
            if leaf[1 + bit_index//8][bit_index % 8]:
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
        return (node_hash, encoded_branch)

    def merkelize(
        self,
        state_dict: Dict[ByteArray32, Bytes],
        db: Optional[KVStore] = None
    ) -> Tuple[NodeHash, Dict[NodeHash, Node]]:
        """
        Implements the state Merklization (per D.2)
        https://graypaper.fluffylabs.dev/#/68eaa1f/39e200393301?v=0.6.4
        
        Fully rebuilds the trie from scratch using the provided key->value map.
        Clears any previous state, invokes the recursive builder, sets root_hash,
        and optionally persists raw key/value blobs into the given KVStore.
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
        Does not touch any external KVStore.
        """
        self.nodes.clear()
        self.root_hash = ZERO_HASH

    def update(self, key: ByteArray32, new_value: Bytes) -> NodeHash:
        """
        Update a single leaf value 'new_value' at 'key', then update only
        the branch nodes on its path, rewiring hashes upward to the root.
        Returns the new root hash.
        """
        self.root_hash = self._recontrust_root(self.root_hash, Node(encoded=encode_leaf(key, new_value)))
        return self.root_hash
    
    def _recontrust_root(self, root: ByteArray32, node: Node, bit_index = 0) -> NodeHash:
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
            
            new_encoded = encode_branch(current_node.left, current_node.right)
            new_parent_hash = NodeHash(Hash.blake2b(bytes(new_encoded)))
            
            self.nodes[new_parent_hash] = Node(
                encoded=new_encoded,
                bit_index=bit_index,
                left=current_node.left,
                right=current_node.right
            )
            
            return new_parent_hash
    
    def __repr__(self):
        return f"StateTrie(root={self.root_hash}, nodes={self.nodes})"