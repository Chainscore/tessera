from typing import Dict, Optional, Literal
from dataclasses import dataclass
from jam.types.protocol.crypto import Hash
from jam.types.base.sequences.bytes import ByteArray32, ByteArray64
from jam.state.merkle.node import Node

NodeHash = ByteArray32
EncodedNode = ByteArray64


# Persistent node type for storing in the ram``.
DBNodeType = Literal["branch", "leaf_embedded", "leaf_normal"]
@dataclass
class DBNode:
    node_type: DBNodeType            
    encoded: ByteArray64            
    key: Optional[ByteArray32] = None  
    bit_index: Optional[int] = None   #TODO: might add later to make it more efficient
    left: Optional[NodeHash] = None    
    right: Optional[NodeHash] = None   

class MerkleTrie:
    """Binary Merkle Trie implementation as defined in D.2
    https://graypaper.fluffylabs.dev/#/68eaa1f/39c40039db00?v=0.6.4
    
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
        #initialize the db_nodes:empty mpt map
        self._db_nodes: Dict[NodeHash, DBNode] = {}
    