from enum import Enum

from tsrkit_types import Uint, U8

from jam.types.protocol.crypto import Hash
from tsrkit_types.bytes import Bytes


ZERO_HASH = Bytes[32]([0] * 32)
NodeHash = Bytes[32]


# Allowed types for DB node objects.
class NodeType(Enum):
    BRANCH = 0
    LEAF_EMBEDDED = 1
    LEAF_NORMAL = 2
    EMPTY = 3


def encode_branch(
    left_hash: Bytes[32] = ZERO_HASH, right_hash: Bytes[32] = ZERO_HASH
) -> Bytes[64]:
    """Encode a branch node (B function in D.3)

    For a branch, we:
    1. Clear the first bit of left_hash (AND with 0xfe)
    2. Concatenate with full right_hash
    """
    return Bytes[64].from_bits(
        [False] + Bytes(left_hash).to_bits()[1:] + right_hash.to_bits()
    )


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
    # First bit is 1 for leaf nodes

    # Set first 31 bytes of key to 1:32
    key_bits = Bytes(key).to_bits()[:248]
    if len(value) <= 32:
        # Embedded value leaf
        # 6-bit - size of value
        # Store key and value
        val_bits = value.to_bits() + [False] * (256 - len(value.to_bits()))
        # Rest is already zeroed
        node_bits = (
            [True, False]
            + Bytes(Uint[8](len(value)).encode()).to_bits()[2:]
            + key_bits
            + val_bits
        )
        return Bytes[64].from_bits(node_bits)
    else:
        # Regular leaf - second bit is 1
        val_bits = Hash.blake2b(bytes(value)).to_bits()
        node_bits = (
            [True, True, False, False, False, False, False, False] + key_bits + val_bits
        )
        return Bytes[64].from_bits(node_bits)
