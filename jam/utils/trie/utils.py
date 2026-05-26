from enum import Enum

from jam.models.protocol.crypto import Hash
from tsrkit_types.bytes import Bytes


Bytes32 = Bytes[32]
Bytes64 = Bytes[64]

ZERO_HASH = Bytes32([0] * 32)
NodeHash = Bytes32


# Allowed types for DB node objects.
class NodeType(Enum):
    BRANCH = 0
    LEAF_EMBEDDED = 1
    LEAF_NORMAL = 2
    EMPTY = 3


def encode_branch(left_hash: Bytes32 = ZERO_HASH, right_hash: Bytes32 = ZERO_HASH) -> Bytes64:
    """Encode a branch node (B function in D.3)

    For a branch, we:
    1. Clear the first bit of left_hash (AND with 0x7F)
    2. Concatenate with full right_hash
    """
    # branch encoding without full bit conversion
    if len(left_hash) != 32 or len(right_hash) != 32:
        raise ValueError("Hash lengths must be 32 bytes")
    
    # Clear first bit of left_hash by AND with 0x7F (01111111)
    result = bytearray(64)
    result[0] = left_hash[0] & 0x7F  # Clear first bit
    result[1:32] = left_hash[1:]     # Copy rest of left hash
    result[32:64] = right_hash       # Copy right hash
    
    return Bytes64(bytes(result))


def encode_leaf(key: Bytes, value: Bytes) -> Bytes[64]:
    """Encode a leaf node (L function in D.4)

    For a leaf, the second bit discriminates between embedded-value leaves and regular leaves.
    For embedded values (|v| ≤ 32):
        - 6 bits store the embedded value size
        - First 31 bytes store key
        - Last 32 bytes store the value (zero-padded)
    For regular leaves:
        - 6 bits are zeroed
        - First 31 bytes store key
        - Last 32 bytes store hash of value
    """
    node = bytearray(64)
    key_part = bytes(key)[:31]
    node[1:1 + len(key_part)] = key_part

    if len(value) <= 32:
        node[0] = 0x80 | len(value)
        node[32:32 + len(value)] = bytes(value)
    else:
        node[0] = 0xC0
        node[32:64] = Hash.blake2b(bytes(value))

    return Bytes64(bytes(node))
