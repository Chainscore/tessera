from typing import Dict, List, Tuple
from jam.types.base.bit import Bit
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

    def bits(self, key: ByteArray32) -> List[Bit]:
        """
        Convert the key into a list of bits from MSB to LSB
        https://graypaper.fluffylabs.dev/#/68eaa1f/071001071101?v=0.6.4
        """
        bits_ = []
        for i in key:
            bits_.extend(i.value)
        return bits_

    def _merkelize_recursive(
        self, items: List[Tuple[ByteArray32, ByteArray32]], bit_index: int
    ) -> Tuple[NodeHash, EncodedNode]:
        """
        Recursive merkelization
        `M` function as defined in D.2 
        https://graypaper.fluffylabs.dev/#/68eaa1f/39e20039e200?v=0.6.4

        Args:
            items: List of tuples containing key-value pairs
            bit_index: Current bit index to split on. We are using bit index instead of slicing bits(key)
            because it's more efficient.

        Returns:
            Tuple containing the node hash and encoded node
        """

        # If we have reached the maximum bit index, means the trie is too big -> throw an error
        if bit_index >= 256:
            raise ValueError("bit_index exceeds maximum value of 255")
        
        # If we have no items, return the zero hash and an empty encoded node 
        # https://graypaper.fluffylabs.dev/#/68eaa1f/391c00391d00?v=0.6.4
        if not items:
            return (self.trie.node.ZERO_HASH, ByteArray64([0] * 64))
        
        # If we have only one item, we can directly encode it as a leaf node `L`
        # https://graypaper.fluffylabs.dev/#/68eaa1f/396100396100?v=0.6.4
        if len(items) == 1:
            key, value = items[0]
            encoded = self.trie.node.encode_leaf(key, value)
            node_hash = NodeHash(self.trie.hash_function(bytes(encoded)))
            self.trie._nodes[node_hash] = encoded
            return (node_hash, encoded)

        # Split items left/right by current bit
        # https://graypaper.fluffylabs.dev/#/68eaa1f/391701393301?v=0.6.4
        left = []
        right = []
        for key, value in items:
            if self.bits(key)[bit_index % len(self.bits(key))]:
                right.append((key, value))
            else:
                left.append((key, value))

        # Recursively merkelize subtrees
        left_hash, left_encoded = self._merkelize_recursive(left, bit_index + 1)
        right_hash, right_encoded = self._merkelize_recursive(right, bit_index + 1)

        # Create branch node `B`
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