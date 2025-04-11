from typing import Dict
from jam.types.protocol.crypto import Hash
from jam.types.base.sequences.bytes import ByteArray32, ByteArray64
from jam.state.merkle.node import Node

NodeHash = ByteArray32
EncodedNode = ByteArray64


class MerkleTrie:
    """Binary Merkle Trie implementation as defined in D.2

    This implements the basic Merklization function Mσ which transforms a serialized
    state mapping into a cryptographic commitment.

    """

    def __init__(self, hash_function: Hash = Hash.blake2b):
        """Initialize an empty Merkle trie with optional hash function"""
        self.node = Node(hash_function)
        self.hash_function = hash_function
        self._nodes: Dict[
            NodeHash, EncodedNode
        ] = (
            {}
        )  # node_hash -> encoded_node - Two node hashes will point to one encoded node
        self._root_hash = self.node.ZERO_HASH
        
    
