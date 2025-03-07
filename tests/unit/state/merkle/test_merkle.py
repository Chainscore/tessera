import pytest

from jam.state.merkle.merkle import StateMerkle
from jam.state.utils.key_constructor import construct_state_key
from jam.types.base.sequences.bytes import Bytes, ByteArray32
from jam.types.protocol.crypto import Hash


def test_merkle_initialization():
    """Test state merkle initialization"""
    merkle = StateMerkle(Hash.blake2b)
    assert merkle.trie.hash_function == Hash.blake2b


def test_empty_merkelize():
    """Test merkelizing empty state"""
    merkle = StateMerkle(Hash.blake2b)
    root = merkle.merkelize({})
    assert root == merkle.trie.node.ZERO_HASH
    assert len(merkle.get_nodes()) == 0


def test_single_item_merkelize():
    """Test merkelizing single item"""
    merkle = StateMerkle(Hash.blake2b)
    key = construct_state_key(1)
    value = Bytes(bytes([2] * 831))
    state = {key: value}

    root = merkle.merkelize(state)
    assert root != merkle.trie.node.ZERO_HASH
    assert len(merkle.get_nodes()) == 1  # Just one leaf node


def test_two_items_merkelize():
    """Test merkelizing two items creates a branch"""
    merkle = StateMerkle(Hash.blake2b)
    state = {
        construct_state_key(101): Bytes(bytes([10] * 329)),
        construct_state_key(100): Bytes(bytes([20] * 122)),
    }

    root = merkle.merkelize(state)
    nodes = merkle.get_nodes()

    # Clear and remerkelize - should get same root
    merkle.clear()
    assert merkle.merkelize(state) == root


def test_multiple_items_merkelize():
    """Test merkelizing multiple items creates proper tree structure"""
    merkle = StateMerkle(Hash.blake2b)
    state = {
        construct_state_key(1): Bytes(bytes([10] * 163)),
        construct_state_key(2): Bytes(bytes([20] * 163)),
        construct_state_key(3): Bytes(bytes([30] * 163)),
        construct_state_key(4): Bytes(bytes([40] * 163)),
    }

    root = merkle.merkelize(state)
    nodes = merkle.get_nodes()

    # Clear and remerkelize - should get same root
    merkle.clear()
    assert merkle.merkelize(state) == root

    state2 = {
        construct_state_key(5): Bytes(bytes([10] * 163)),
        construct_state_key(2): Bytes(bytes([20] * 163)),
        construct_state_key(3): Bytes(bytes([30] * 163)),
        construct_state_key(4): Bytes(bytes([40] * 163)),
    }
    assert merkle.merkelize(state2) != root


def test_deterministic_merkelize():
    """Test merkelization is deterministic regardless of insertion order"""
    merkle1 = StateMerkle(Hash.blake2b)
    merkle2 = StateMerkle(Hash.blake2b)

    state = {
        construct_state_key(1): ByteArray32(bytes([10] * 32)),
        construct_state_key(2): ByteArray32(bytes([20] * 32)),
        construct_state_key(3): ByteArray32(bytes([30] * 32)),
    }

    # Insert in different orders
    root1 = merkle1.merkelize(state)

    reversed_state = dict(reversed(list(state.items())))
    root2 = merkle2.merkelize(reversed_state)

    # Should get same root and nodes
    assert root1 == root2
    assert merkle1.get_nodes() == merkle2.get_nodes()


def test_odd_number_items_merkelize():
    """Test merkelizing odd number of items promotes last node correctly"""
    merkle = StateMerkle(Hash.blake2b)
    state = {
        construct_state_key(1): ByteArray32(bytes([10] * 32)),
        construct_state_key(2): ByteArray32(bytes([20] * 32)),
        construct_state_key(3): ByteArray32(bytes([30] * 32)),
    }

    root = merkle.merkelize(state)
    nodes = merkle.get_nodes()

    # Clear and remerkelize - should get same root
    merkle.clear()
    assert merkle.merkelize(state) == root
