from jam.utils.trie.merkle import StateTrie as StateMerkle
from jam.utils.trie.utils import ZERO_HASH
from jam.state.utils import construct_state_key
from tsrkit_types import Bytes


def test_empty_merkelize():
    """Test merkelizing empty state"""
    merkle = StateMerkle()
    root,_ = merkle.merkelize({})
    assert root == ZERO_HASH
    assert len(merkle.get_nodes()) == 0


def test_single_item_merkelize():
    """Test merkelizing single item"""
    merkle = StateMerkle()
    key = construct_state_key(1)
    value = Bytes(bytes([2] * 831))
    state = {key: value}

    root = merkle.merkelize(state)
    assert root != ZERO_HASH
    assert len(merkle.get_nodes()) == 1  # Just one leaf node


def test_two_items_merkelize():
    """Test merkelizing two items creates a branch"""
    merkle = StateMerkle()
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
    merkle = StateMerkle()
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
    merkle1 = StateMerkle()
    merkle2 = StateMerkle()

    state = {
        construct_state_key(1): Bytes[32](bytes([10] * 32)),
        construct_state_key(2): Bytes[32](bytes([20] * 32)),
        construct_state_key(3): Bytes[32](bytes([30] * 32)),
    }

    # Insert in different orders
    root1 , _= merkle1.merkelize(state)

    reversed_state = dict(reversed(list(state.items())))
    root2, _ = merkle2.merkelize(reversed_state)

    # Should get same root and nodes
    assert root1 == root2
    assert merkle1.get_nodes() == merkle2.get_nodes()


def test_odd_number_items_merkelize():
    """Test merkelizing odd number of items promotes last node correctly"""
    merkle = StateMerkle()
    state = {
        construct_state_key(1): Bytes[32](bytes([10] * 32)),
        construct_state_key(2): Bytes[32](bytes([20] * 32)),
        construct_state_key(3): Bytes[32](bytes([30] * 32)),
    }

    root, _ = merkle.merkelize(state)
    nodes = merkle.get_nodes()

    # Clear and remerkelize - should get same root
    merkle.clear()
    assert merkle.merkelize(state)[0] == root
