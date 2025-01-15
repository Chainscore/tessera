import pytest

from jam.state.state import State
from jam.types.protocol.crypto import Hash, ByteArray32

def test_state_initialization(dummy_state_components):
    """Test state initialization"""
    state = State(**dummy_state_components)
    assert state._merkle.trie.hash_function == Hash.blake2b

def test_state_merkelize(dummy_state_components):
    """Test state merklization"""
    state1 = State(**dummy_state_components)
    state2 = State(**dummy_state_components)
    
    # States with same components should have same root
    root1 = state1.merkelize()
    root2 = state2.merkelize()
    assert root1 == root2
    assert root1 != state1._merkle.trie.node.ZERO_HASH
    
    # Verify all components are included
    nodes = state1.get_merkle_nodes()
    assert len(nodes) > 0
    
def test_state_merkle_nodes(dummy_state_components):
    """Test accessing merkle nodes from state"""
    state = State(**dummy_state_components)
    
    # Get initial root
    root = state.merkelize()
    
    # Get nodes and verify root node exists
    nodes = state.get_merkle_nodes()
    assert len(nodes) > 0  # Should have at least one node
    
    # Clear merkle and verify nodes are gone
    state._merkle.clear()
    assert len(state.get_merkle_nodes()) == 0

def test_state_transform(dummy_state_components):
    """Test state transformation to dictionary"""
    state = State(**dummy_state_components)
    
    # Transform state to dictionary
    state_dict = state.transform()
    
    # Verify all components are included
    assert len(state_dict) == 8  # Currently only 8 components in transform()
    
    # Verify keys are properly constructed
    for i in range(1, 9):
        assert any(k.startswith(bytes([i])) for k in state_dict.keys()) 


def test_state_root(dummy_state_components):
    """Test the state root generation"""
    state = State(**dummy_state_components)
    root = state.generate_root()
    assert isinstance(root, ByteArray32)
    assert len(root) == 32