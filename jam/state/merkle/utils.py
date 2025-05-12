from enum import Enum
from typing import Literal
from jam.types.base.bit import Bit
from jam.types.base.sequences.bytes.bit_array import Byte
from jam.types.base.sequences.bytes.byte_array import ByteArray32, ByteArray64
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.protocol.crypto import Hash
from jam.utils.byte_utils import ByteUtils

ZERO_HASH = ByteArray32([Byte(0)] * 32)
NodeHash = ByteArray32

# Allowed types for DB node objects.
class NodeType(Enum):
    BRANCH           = 0
    LEAF_EMBEDDED    = 1
    LEAF_NORMAL      = 2
    EMPTY            = 3


def encode_branch(left_hash: ByteArray32, right_hash: ByteArray32) -> ByteArray64:
    """Encode a branch node (B function in D.3)

    For a branch, we:
    1. Clear the first bit of left_hash (AND with 0xfe)
    2. Concatenate with full right_hash
    """
    # Clear first bit of left hash (AND with 0xfe)
    modified_left = ByteArray32(left_hash)
    modified_left[0][0] = Bit(0)

    # Combine the modified left and right hashes
    node = ByteArray64([0] * 64)
    node[0:32] = modified_left
    node[32:64] = right_hash

    return node

def encode_leaf(key: ByteArray32, value: Bytes) -> ByteArray64:
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
    # First bit is 1 for leaf nodes
    node = ByteArray64([0] * 64)  # 512 bits total, first bit set
    # Set first 31 bytes of key to 1:32
    node[0][0] = Bit(1)
    node[1:32] = key[:31]

    if len(value) <= 32:
        # Embedded value leaf

        # 6-bit - size of value
        encoded_size = Byte(len(value))
        node[0][2:8] = encoded_size[2:8]

        # Store key and value
        node[1:32] = key[:31]  # First 31 bytes for key
        node[32 : 32 + len(value)] = value  # Value bytes
        # Rest is already zeroed
    else:
        # Regular leaf - second bit is 1
        node[0][1] = Bit(1)

        node[1:32] = key[:31]  # First 31 bytes for key
        node[32:] = Hash.blake2b(
            bytes(value)
        )
    return node