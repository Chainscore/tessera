import pytest
from jam.types.base.sequences.bytes.byte_array import (
    ByteArray8, ByteArray16, ByteArray32, ByteArray64,
    ByteArray96, ByteArray128, ByteArray144, ByteArray256, ByteArray784
)
from jam.utils.json.serde import JsonDeserializationError
def test_byte_array_json_serialization_hex():
    # Test serialization of hex strings
    data = "0x1234123412341234"
    array = ByteArray8(data)
    json_data = array.to_json()
    assert json_data == data
    
    reconstructed = ByteArray8.from_json(json_data)
    assert reconstructed == array
    assert bytes(reconstructed) == bytes.fromhex("1234123412341234")

def test_byte_array_json_serialization_bytes():
    # Test serialization of raw bytes
    data = bytes([0x12, 0x34, 0x56, 0x78, 0x12, 0x34, 0x56, 0x78])
    array = ByteArray8(data)
    json_data = array.to_json()
    assert json_data == "0x1234567812345678"
    
    reconstructed = ByteArray8.from_json(json_data)
    assert reconstructed == array
    assert bytes(reconstructed) == data

def test_byte_array_json_fixed_lengths():
    # Test different fixed-length byte arrays
    test_cases = [
        (ByteArray8, "0x" + "ff" * 8),
        (ByteArray16, "0x" + "ff" * 16),
        (ByteArray32, "0x" + "ff" * 32),
        (ByteArray64, "0x" + "ff" * 64),
        (ByteArray96, "0x" + "ff" * 96),
        (ByteArray128, "0x" + "ff" * 128),
        (ByteArray144, "0x" + "ff" * 144),
        (ByteArray256, "0x" + "ff" * 256),
        (ByteArray784, "0x" + "ff" * 784)
    ]
    
    for array_class, hex_str in test_cases:
        array = array_class(hex_str)
        json_data = array.to_json()
        assert json_data == hex_str.lower()
        
        reconstructed = array_class.from_json(json_data, )
        assert reconstructed == array
        assert len(bytes(reconstructed)) == len(hex_str[2:]) // 2

def test_byte_array_json_invalid_input():
    # Test with invalid hex strings
    with pytest.raises(ValueError):
        ByteArray8.from_json("not hex")
    
    with pytest.raises(ValueError):
        ByteArray8.from_json("0xZZ")  # Invalid hex characters
    
    # Test with wrong length
    with pytest.raises(ValueError):
        ByteArray8.from_json("0x" + "ff" * 4)  # Too short
    
    with pytest.raises(ValueError):
        ByteArray8.from_json("0x" + "ff" * 16)  # Too long
    
    # Test with invalid types
    with pytest.raises(ValueError):
        ByteArray8.from_json(123)  # Integer instead of hex string
    
    with pytest.raises(TypeError):
        ByteArray8.from_json(None)  # None instead of hex string
    
    with pytest.raises(ValueError):
        ByteArray8.from_json([])  # List instead of hex string

def test_byte_array_json_roundtrip():
    # Test roundtrip with different patterns
    test_patterns = [
        "0x" + "00" * 8,  # All zeros
        "0x" + "ff" * 8,  # All ones
        "0x0123456789abcdef",  # Sequential
        "0xdeadbeefdeadbeef"   # Common pattern
    ]
    
    for pattern in test_patterns:
        original = ByteArray8(pattern)
        json_data = original.to_json()
        assert json_data == pattern.lower()
        
        reconstructed = ByteArray8.from_json(json_data)
        assert reconstructed == original
        assert bytes(reconstructed) == bytes.fromhex(pattern[2:])

def test_byte_array_json_operations():
    # Test that JSON serialized and deserialized byte arrays maintain operations
    original = ByteArray8("0x1234567890abcdef")
    json_data = original.to_json()
    reconstructed = ByteArray8.from_json(json_data)
    
    # Test integer conversion
    assert int(reconstructed) == int(original)
    assert reconstructed.to_int() == original.to_int()
    assert reconstructed.to_int("little") == original.to_int("little")
    
    # Test indexing
    assert reconstructed[0] == original[0]
    assert reconstructed[-1] == original[-1]
    
    # Test slicing
    assert reconstructed[1:3] == original[1:3]
    
    # Test iteration
    assert list(reconstructed) == list(original)
    
    # Test length
    assert len(reconstructed) == len(original)

def test_byte_array_json_case_insensitivity():
    # Test that hex strings are case insensitive
    upper = ByteArray8("0xDEADBEEFDEADBEEF")
    lower = ByteArray8("0xdeadbeefdeadbeef")
    mixed = ByteArray8("0xDeAdBeEfDeAdBeEf")
    
    assert upper.to_json() == lower.to_json() == mixed.to_json()
    
    # Test deserialization with different cases
    json_upper = "0xDEADBEEFDEADBEEF"
    json_lower = "0xdeadbeefdeadbeef"
    json_mixed = "0xDeAdBeEfDeAdBeEf"
    
    assert ByteArray8.from_json(json_upper) == ByteArray8.from_json(json_lower)
    assert ByteArray8.from_json(json_lower) == ByteArray8.from_json(json_mixed)

def test_byte_array_json_prefix_handling():
    # Test handling of "0x" prefix
    with_prefix = "0x1234123412341234"
    without_prefix = "1234123412341234"
    
    array1 = ByteArray8(with_prefix)
    array2 = ByteArray8(without_prefix)
    
    assert array1 == array2
    assert array1.to_json() == with_prefix  # Should always include prefix
    assert ByteArray8.from_json(with_prefix) == ByteArray8.from_json(without_prefix) 