"""
Unit tests for dictionary codec implementation.
"""

import pytest
from typing import Dict, Mapping
from jam.utils.codec.composite.dictionaries import DictionaryCodec
from jam.utils.codec.base import EncodeError, DecodeError
from jam.utils.codec.primitives.integers import general_codec
from jam.utils.codec.primitives.strings import string_codec
from jam.utils.codec.primitives.bools import boolean_codec

class TestDictionaryCodec:
    """Test suite for dictionary encoding/decoding."""

    def test_empty_dict(self):
        """Test encoding/decoding of empty dictionaries."""
        codec = DictionaryCodec(str, int, string_codec, general_codec)
        value = {}
        encoded = codec.encode(value)
        # Should just be length byte (0)
        assert encoded == bytes([0])
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == 1

    @pytest.mark.parametrize("length", [
        0xFC,    # Maximum single-byte length
        0xFD,    # Start of two-byte length
        0xFF,    # Edge within two-byte length
        0xFFFF,  # Maximum two-byte length
    ])
    def test_length_encoding_boundaries(self, length):
        """Test dictionary encoding at length boundaries."""
        codec = DictionaryCodec(str, int, string_codec, general_codec)
        value = {str(i): i for i in range(length)}
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert len(decoded) == length
        assert decoded == value

    @pytest.mark.parametrize("key_type,value_type,key_codec,value_codec,sample", [
        (str, int, string_codec, general_codec, {"a": 1, "b": 2}),
        (int, bool, general_codec, boolean_codec, {1: True, 2: False}),
        (str, str, string_codec, string_codec, {"hello": "world"}),
    ])
    def test_various_types(self, key_type, value_type, key_codec, value_codec, sample):
        """Test dictionary codec with various key/value types."""
        codec = DictionaryCodec(key_type, value_type, key_codec, value_codec)
        encoded = codec.encode(sample)
        decoded, size = codec.decode_from(encoded)
        assert decoded == sample
        assert size == len(encoded)

    def test_nested_dictionaries(self):
        """Test encoding/decoding of nested dictionaries."""
        inner_codec = DictionaryCodec(str, int, string_codec, general_codec)
        outer_codec = DictionaryCodec(str, dict, string_codec, inner_codec)
        
        value = {
            "first": {"a": 1, "b": 2},
            "second": {"c": 3, "d": 4}
        }
        
        encoded = outer_codec.encode(value)
        decoded, size = outer_codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_deterministic_encoding(self):
        """Test that dictionary encoding is deterministic (same dict = same bytes)."""
        codec = DictionaryCodec(str, int, string_codec, general_codec)
        dict1 = {"b": 2, "a": 1, "c": 3}
        dict2 = {"a": 1, "c": 3, "b": 2}
        
        encoded1 = codec.encode(dict1)
        encoded2 = codec.encode(dict2)
        assert encoded1 == encoded2

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = DictionaryCodec(str, int, string_codec, general_codec)
        value = {"a": 1, "b": 2}
        size = codec.encode_size(value)
        
        # Test encoding into too small buffer
        with pytest.raises(EncodeError):
            codec.encode_into(value, bytearray(size - 1))
        
        # Test decoding from too small buffer
        encoded = codec.encode(value)
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                codec.decode_from(encoded[:i])

    def test_invalid_types(self):
        """Test handling of invalid value types."""
        codec = DictionaryCodec(str, int, string_codec, general_codec)
        
        invalid_values = [
            42,              # int
            "not a dict",    # str
            [1, 2, 3],      # list
            {1, 2, 3},      # set
            None,           # None
        ]
        
        for value in invalid_values:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_invalid_key_value_types(self):
        """Test handling of invalid key/value types."""
        codec = DictionaryCodec(str, int, string_codec, general_codec)
        
        invalid_dicts = [
            {42: "wrong"},           # wrong key type
            {"key": "wrong"},        # wrong value type
            {None: 1},               # wrong key type
            {"key": None},           # wrong value type
            {True: "wrong"},         # wrong key type
        ]
        
        for value in invalid_dicts:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        codec = DictionaryCodec(str, int, string_codec, general_codec)
        value = {"a": 1, "b": 2}
        size = codec.encode_size(value)
        
        # Create buffer with padding
        buffer = bytearray([0xFF] * (size + 2))
        
        # Test encoding at offset
        written = codec.encode_into(value, buffer, 1)
        assert written == size
        
        # Test decoding at offset
        decoded, read = codec.decode_from(buffer, 1)
        assert decoded == value
        assert read == size
        
        # Verify padding wasn't overwritten
        assert buffer[0] == 0xFF
        assert buffer[-1] == 0xFF

    def test_duplicate_keys(self):
        """Test handling of duplicate keys during decoding."""
        codec = DictionaryCodec(str, int, string_codec, general_codec)
        
        # Create encoded data with duplicate keys (manually)
        encoded = bytes([2]) + codec.key_codec.encode("a") + codec.value_codec.encode(1) + \
                 codec.key_codec.encode("a") + codec.value_codec.encode(2)
        
        with pytest.raises(DecodeError) as exc_info:
            codec.decode_from(encoded)
        assert "Duplicate key" in str(exc_info.value)

    def test_string_key_values(self):
        """Test dictionaries with string keys and values with various content."""
        codec = DictionaryCodec(str, str, string_codec, string_codec)
        test_values = {
            "": "",                    # Empty strings
            "hello": "world",          # ASCII
            "🦀": "Rust",              # Unicode
            "key": "a" * 1000,         # Long string
            "unicode": "Hello, 世界！"  # Mixed ASCII and Unicode
        }
        
        encoded = codec.encode(test_values)
        decoded, size = codec.decode_from(encoded)
        assert decoded == test_values
        assert size == len(encoded)

    def test_complex_nested_structure(self):
        """Test complex nested dictionary structures."""
        from jam.utils.codec.composite.vectors import VectorCodec
        
        # Create Dict[str, Dict[str, List[int]]] codec
        inner_list_codec = VectorCodec(int, general_codec)
        inner_dict_codec = DictionaryCodec(str, list, string_codec, inner_list_codec)
        outer_codec = DictionaryCodec(str, dict, string_codec, inner_dict_codec)
        
        value = {
            "first": {
                "a": [1, 2, 3],
                "b": []
            },
            "second": {
                "c": [4, 5]
            }
        }
        
        encoded = outer_codec.encode(value)
        decoded, size = outer_codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded) 