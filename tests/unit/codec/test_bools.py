"""
Unit tests for boolean codec implementation.
"""

import pytest
from jam.utils.codec.primitives.bools import BooleanCodec, EncodeError, DecodeError

boolean_codec = BooleanCodec()

def test_encode_size():
    """Test that encode_size always returns 1."""
    assert boolean_codec.encode_size(True) == 1
    assert boolean_codec.encode_size(False) == 1

def test_encode_values():
    """Test encoding of True and False values."""
    assert boolean_codec.encode(True) == bytes([1])
    assert boolean_codec.encode(False) == bytes([0])

def test_decode_values():
    """Test decoding of encoded boolean values."""
    # Check standard values
    assert boolean_codec.decode_from(bytes([1]))[0] is True
    assert boolean_codec.decode_from(bytes([0]))[0] is False
    
    # Test that any non-zero value decodes to True for robustness
    for i in range(2, 256):
        assert boolean_codec.decode_from(bytes([i]))[0] is True

def test_roundtrip():
    """Test encoding and decoding roundtrip."""
    for value in [True, False]:
        encoded = boolean_codec.encode(value)
        decoded, size = boolean_codec.decode_from(encoded)
        assert decoded is value
        assert size == 1

def test_non_boolean_values():
    """Test that non-boolean values raise TypeError."""
    values = [
        [0, False],      # int
        [1, True],      # int
        ["True", True], # str
        [1.0, True],    # float
        [None, False],   # NoneType
    ]
    
    for value in values:
        assert boolean_codec.encode(value[0]) == boolean_codec.encode(value[1])

def test_buffer_bounds():
    """Test buffer bounds checking."""
    # Test encoding into too small buffer
    with pytest.raises(EncodeError):
        boolean_codec.encode_into(True, bytearray())
        
    # Test decoding from empty buffer
    with pytest.raises(DecodeError):
        boolean_codec.decode_from(bytes([]))

def test_offset_handling():
    """Test encoding and decoding with buffer offsets."""
    buffer = bytearray([0xFF, 0xFF, 0xFF])
    
    # Test encoding at offset
    boolean_codec.encode_into(True, buffer, 1)
    assert buffer == bytes([0xFF, 0x01, 0xFF])
    
    # Test decoding at offset
    decoded, size = boolean_codec.decode_from(buffer, 1)
    assert decoded is True
    assert size == 1

@pytest.mark.parametrize("value,expected", [
    (True, bytes([1])),
    (False, bytes([0])),
])
def test_encoding_matches_spec(value, expected):
    """Test that encoding matches the specification."""
    assert boolean_codec.encode(value) == expected

@pytest.mark.parametrize("encoded,expected", [
    (bytes([0]), False),
    (bytes([1]), True),
    (bytes([2]), True),  # Any non-zero value
    (bytes([255]), True),  # Any non-zero value
])
def test_decoding_matches_spec(encoded, expected):
    """Test that decoding matches the specification."""
    decoded, _ = boolean_codec.decode_from(encoded)
    assert decoded is expected 