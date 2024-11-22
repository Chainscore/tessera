"""
Unit tests for boolean codec implementation.
"""

import pytest
from jam.core.codec.primitives.bools import codec, EncodeError, DecodeError


def test_encode_size():
    """Test that encode_size always returns 1."""
    assert codec.encode_size(True) == 1
    assert codec.encode_size(False) == 1


def test_encode_values():
    """Test encoding of True and False values."""
    assert codec.encode(True) == bytes([1])
    assert codec.encode(False) == bytes([0])


def test_decode_values():
    """Test decoding of encoded boolean values."""
    # Check standard values
    assert codec.decode_from(bytes([1]))[0] is True
    assert codec.decode_from(bytes([0]))[0] is False
    
    # Test that any non-zero value decodes to True for robustness
    for i in range(2, 256):
        assert codec.decode_from(bytes([i]))[0] is True


def test_roundtrip():
    """Test encoding and decoding roundtrip."""
    for value in [True, False]:
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded is value
        assert size == 1


def test_invalid_type():
    """Test that non-boolean values raise TypeError."""
    invalid_values = [
        0,      # int
        1,      # int
        "True", # str
        1.0,    # float
        None,   # NoneType
    ]
    
    for value in invalid_values:
        with pytest.raises(EncodeError):
            codec.encode(value)


def test_buffer_bounds():
    """Test buffer bounds checking."""
    # Test encoding into too small buffer
    with pytest.raises(EncodeError):
        codec.encode_into(True, bytearray())
        
    # Test decoding from empty buffer
    with pytest.raises(DecodeError):
        codec.decode_from(bytes([]))


def test_codec_registry():
    """Test that bool codec is properly registered."""
    from jam.core.codec.base import CodecRegistry
    
    # Check registration
    assert CodecRegistry.get(bool) is codec
    
    # Test encoding through registry
    assert CodecRegistry.encode(True) == bytes([1])
    assert CodecRegistry.encode(False) == bytes([0])
    
    # Test decoding through registry
    decoded, _ = CodecRegistry.decode(bool, bytes([1]))
    assert decoded is True
    decoded, _ = CodecRegistry.decode(bool, bytes([0]))
    assert decoded is False


def test_offset_handling():
    """Test encoding and decoding with buffer offsets."""
    buffer = bytearray([0xFF, 0xFF, 0xFF])
    
    # Test encoding at offset
    codec.encode_into(True, buffer, 1)
    assert buffer == bytes([0xFF, 0x01, 0xFF])
    
    # Test decoding at offset
    decoded, size = codec.decode_from(buffer, 1)
    assert decoded is True
    assert size == 1


@pytest.mark.parametrize("value,expected", [
    (True, bytes([1])),
    (False, bytes([0])),
])
def test_encoding_matches_spec(value, expected):
    """Test that encoding matches the specification."""
    assert codec.encode(value) == expected


@pytest.mark.parametrize("encoded,expected", [
    (bytes([0]), False),
    (bytes([1]), True),
    (bytes([2]), True),  # Any non-zero value
    (bytes([255]), True),  # Any non-zero value
])
def test_decoding_matches_spec(encoded, expected):
    """Test that decoding matches the specification."""
    decoded, _ = codec.decode_from(encoded)
    assert decoded is expected