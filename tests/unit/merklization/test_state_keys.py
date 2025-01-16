import pytest
from jam.state.utils.key_constructor import construct_state_key
from jam.types.base.integers.fixed import U8
from jam.types.base.sequences.byte_array import ByteArray32
from jam.types.protocol.core import ServiceId

def test_single_u8_index():
    """Test case 1: Single U8 index -> [i, 0, 0, ...]"""
    # Test with various U8 values
    test_cases = [
        U8(0),
        U8(1),
        U8(127),
        U8(255)
    ]
    
    for index in test_cases:
        result = construct_state_key(index)
        assert isinstance(result, ByteArray32)
        assert len(result) == 32
        assert result[0] == index
        # Verify rest is zeros
        assert all(b == 0 for b in result[1:])

def test_u32_service_id_pair():
    """Test case 2: (U32, ServiceId) -> [i, n₀, 0, n₁, 0, n₂, 0, n₃, 0, 0, ...]"""
    # Create test service IDs
    service_id1 = ServiceId(1)  # Assuming ServiceId takes an integer
    service_id2 = ServiceId(255)
    
    test_cases = [
        (U8(0), service_id1),
        (U8(1), service_id1),
        (U8(0xFF), service_id1),
        (U8(0), service_id2),
    ]
    
    for index, service_id in test_cases:
        result = construct_state_key((index, service_id))
        assert isinstance(result, ByteArray32)
        assert len(result) == 32
        
        # # Verify index bytes
        index_bytes = index.encode()
        assert result[0] == index_bytes
        
        # Verify service ID encoding pattern
        service_id_encoded = service_id.encode()
        for i, byte in enumerate(service_id_encoded):
            pos = 1 + i * 2  # Skip index bytes and account for zero padding
            if pos < 32:
                assert result[pos] == byte
                if pos + 1 < 32:
                    assert result[pos + 1] == 0  # Verify zero padding

def test_service_id_hash_pair():
    """Test case 3: (ServiceId, ByteArray32) -> [n₀, h₀, n₁, h₁, n₂, h₂, n₃, h₃, h₄, h₅, ..., h₂₇]"""
    service_id = ServiceId(1)
    hash_bytes = ByteArray32([i % 256 for i in range(32)])  # Test pattern
    
    result = construct_state_key((service_id, hash_bytes))
    assert isinstance(result, ByteArray32)
    assert len(result) == 32
    
    service_id_encoded = service_id.encode()
    
    # Check interleaved pattern for first 4 service ID bytes
    for i in range(min(len(service_id_encoded), 4)):
        assert result[i*2] == service_id_encoded[i]
        assert result[i*2 + 1] == hash_bytes[i]
    
    # Check remaining hash bytes
    assert result[8:] == hash_bytes[4:-4]

def test_invalid_inputs():
    """Test error cases with invalid inputs"""
    with pytest.raises(ValueError, match="Invalid input type"):
        construct_state_key("invalid")  # String input
        
    with pytest.raises(ValueError, match="Invalid tuple input types"):
        construct_state_key((U8(1), U8(2)))  # Wrong tuple types
        
    with pytest.raises(ValueError, match="Invalid tuple input types"):
        construct_state_key((ServiceId(1), "not_bytes"))  # Wrong second tuple element

def test_boundary_conditions():
    """Test boundary conditions and edge cases"""
    # Test with minimum values
    assert len(construct_state_key(U8(0))) == 32
    assert len(construct_state_key((U8(0), ServiceId(0)))) == 32
    assert len(construct_state_key((ServiceId(0), ByteArray32([0]*32)))) == 32
    
    # Test with maximum values
    assert len(construct_state_key(U8(255))) == 32
    assert len(construct_state_key((U8(0xFF), ServiceId(255)))) == 32
    assert len(construct_state_key((ServiceId(255), ByteArray32([255]*32)))) == 32
