import pytest

from jam.state.merkle.node import Node
from jam.types.base.byte import Byte
from jam.types.base.bytes import Bytes
from jam.types.protocol.crypto import Hash, ByteArray32

def test_node_initialization():
    """Test node initialization with and without hash function"""
    node = Node()
    assert node.hash_function == Hash.blake2b
    
    node = Node(Hash.sha256)
    assert node.hash_function == Hash.sha256

def test_encode_branch():
    """Test branch node encoding"""
    node = Node()
    left_hash = ByteArray32(bytes([1] * 32))
    right_hash = ByteArray32(bytes([2] * 32))
    
    encoded = node.encode_branch(left_hash, right_hash)
    
    # Check size and first bit
    assert len(encoded) == node.NODE_SIZE
    assert encoded[0].to_bit_array()[0] == 0  # First bit should be 0
    
    # Check hash contents
    assert encoded[1:32] == left_hash[:31]  # First 31 bytes of left hash
    assert encoded[31] == left_hash[30]  # Last 7 bits of left hash
    assert encoded[32:] == right_hash  # Full right hash

def test_encode_leaf_embedded():
    """Test leaf node encoding with embedded value"""
    node = Node()
    key = ByteArray32([3] * 32)
    value = Bytes([4] * 16)  # 16 byte value (fits in embedded)
    
    encoded = node.encode_leaf(key, value)
    
    # Check size and bits
    assert len(encoded) == node.NODE_SIZE
    assert encoded[0].to_bit_array()[0] == 1  # First bit should be 1
    assert encoded[0].to_bit_array()[1] == 0  # Second bit should be 1 for embedded
    assert Byte(encoded[0].to_bit_array()[2:8]).value == len(value)  # Size bits should match value length
    
    # Check contents
    assert encoded[1:32] == key[:-1]  # Key bytes
    assert encoded[32:32+len(value)] == value  # Value bytes
    assert encoded[32+len(value):] == Bytes([0] * (32-len(value)))  # Rest should be zero

def test_encode_leaf_regular():
    """Test leaf node encoding with hashed value"""
    node = Node(Hash.blake2b)
    key = ByteArray32([5] * 32)
    value = Bytes([6] * 64)  # 64 byte value (too big for embedded)
    
    encoded = node.encode_leaf(key, value)
    
    # Check size and bits
    assert len(encoded) == node.NODE_SIZE
    assert encoded[0].to_bit_array()[0] == 1  # First bit should be 1
    assert encoded[0].to_bit_array()[1] == 1  # Second bit should be 0 for regular
    
    # Check contents
    assert encoded[1:32] == key[0:31]  # Key bytes
    assert encoded[32:] == node.hash_function(bytes(value))  # Value hash 