"""
Unit tests for dictionary codec implementation.
"""

import pytest
from typing import Dict as PyDict
from jam.core.codec.composite.dictionaries import (
    Dict, DictionaryCodec, make_dict_codec, register_dict_type,
    EncodeError, DecodeError
)

class TestDictionaryCodec:
    """Test suite for dictionary encoding/decoding."""

    def test_empty_dict(self):
        """Test encoding/decoding of empty dictionaries."""
        codec = Dict[str, int]
        value = {}
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)
        # Should just be length byte (0)
        assert encoded[0] == 0

    @pytest.mark.parametrize("items", [
        {"a": 1},                      # Single item
        {"a": 1, "b": 2},             # Two items
        {str(i): i for i in range(5)}  # Multiple items
    ])
    def test_various_sizes(self, items):
        """Test dictionaries of different sizes."""
        codec = Dict[str, int]
        encoded = codec.encode(items)
        decoded, size = codec.decode_from(encoded)
        assert decoded == items
        assert size == len(encoded)

    @pytest.mark.parametrize("key_type,value_type,items", [
        (str, int, {"a": 1, "b": 2}),
        (int, str, {1: "a", 2: "b"}),
        (str, bool, {"a": True, "b": False}),
        (bool, int, {True: 1, False: 0}),
        (str, float, {"a": 1.0, "b": 2.5}),
    ])
    def test_various_types(self, key_type, value_type, items):
        """Test dictionary codec with various key and value types."""
        codec = Dict[key_type, value_type]
        encoded = codec.encode(items)
        decoded, size = codec.decode_from(encoded)
        assert decoded == items
        assert size == len(encoded)

    def test_deterministic_encoding(self):
        """Test that dictionary encoding is deterministic (same dict = same bytes)."""
        codec = Dict[str, int]
        dict1 = {"b": 2, "a": 1, "c": 3}  # Different order
        dict2 = {"a": 1, "b": 2, "c": 3}  # Different order
        
        encoded1 = codec.encode(dict1)
        encoded2 = codec.encode(dict2)
        
        assert encoded1 == encoded2  # Encoding should be the same

    def test_nested_dicts(self):
        """Test encoding/decoding of nested dictionaries."""
        inner_codec = Dict[str, int]
        outer_codec = DictionaryCodec(str, dict, None, inner_codec)
        
        value = {
            "first": {"a": 1, "b": 2},
            "second": {"c": 3, "d": 4}
        }
        
        encoded = outer_codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_invalid_types(self):
        """Test handling of invalid types."""
        codec = Dict[str, int]
        
        invalid_values = [
            42,              # int
            "not a dict",    # str
            [1, 2, 3],       # list
            {1, 2, 3},       # set
            None,            # None
        ]
        
        for value in invalid_values:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_invalid_key_types(self):
        """Test handling of invalid key types."""
        codec = Dict[str, int]
        
        invalid_dicts = [
            {1: 1},          # int key when str expected
            {True: 1},       # bool key when str expected
            {None: 1},       # None key when str expected
            {"a": 1, 2: 2},  # Mixed valid/invalid keys
        ]
        
        for value in invalid_dicts:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_invalid_value_types(self):
        """Test handling of invalid value types."""
        codec = Dict[str, int]
        
        invalid_dicts = [
            {"a": "str"},     # str value when int expected
            {"a": True},      # bool value when int expected
            {"a": None},      # None value when int expected
            {"a": 1, "b": "str"}  # Mixed valid/invalid values
        ]
        
        for value in invalid_dicts:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = Dict[str, int]
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

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        codec = Dict[str, int]
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

    def test_dict_constructors(self):
        """Test different ways of creating dictionary codecs."""
        value = {"a": 1, "b": 2}
        
        # Using Dict type syntax
        codec1 = Dict[str, int]
        
        # Using make_dict_codec function
        codec2 = make_dict_codec(str, int)
        
        # Using DictionaryCodec constructor
        codec3 = DictionaryCodec(str, int)
        
        # All should produce identical results
        encoded1 = codec1.encode(value)
        encoded2 = codec2.encode(value)
        encoded3 = codec3.encode(value)
        
        assert encoded1 == encoded2 == encoded3

    def test_registry_integration(self):
        """Test integration with codec registry."""
        from jam.core.codec.base import CodecRegistry
        
        # Register dictionary type
        dict_type = PyDict[str, int]
        register_dict_type(dict_type)
        
        # Test encoding through registry
        value = {"a": 1, "b": 2}
        codec = CodecRegistry.get(dict_type)
        assert codec is not None
        
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value

    def test_string_handling(self):
        """Test dictionaries with various string content."""
        codec = Dict[str, str]
        test_values = {
            "empty_key": "",         # Empty string value
            "": "empty_value",       # Empty string key
            "unicode": "🦀 Rust",    # Unicode value
            "long": "a" * 1000,      # Long string value
            "mixed": "Hello, 世界"   # Mixed string value
        }
        
        encoded = codec.encode(test_values)
        decoded, size = codec.decode_from(encoded)
        assert decoded == test_values
        assert size == len(encoded)

    def test_duplicate_keys(self):
        """Test that duplicate keys are detected during decoding."""
        codec = Dict[str, int]
        
        # Create encoded data with duplicate keys (by manipulating the encoding)
        valid = codec.encode({"a": 1})
        duplicated = codec.encode({"a": 2})
        
        # Combine them (this is a bit hacky and implementation-dependent)
        # We modify the length prefix and concatenate the entries
        combined = bytearray([2]) + valid[1:] + duplicated[1:]
        
        with pytest.raises(DecodeError) as exc_info:
            codec.decode_from(combined)
        assert "Duplicate key" in str(exc_info.value)

    def test_partial_decode_failure(self):
        """Test handling of decode failures partway through dictionary."""
        codec = Dict[str, int]
        
        # Create valid encoding and corrupt it
        valid = codec.encode({"a": 1, "b": 2})
        corrupted = valid[:-1]  # Remove last byte
        
        with pytest.raises(DecodeError) as exc_info:
            codec.decode_from(corrupted)
        assert "Failed to decode dictionary" in str(exc_info.value)

    def test_complex_types(self):
        """Test dictionaries with complex value types."""
        from jam.core.codec.composite.options import Option
        from jam.core.codec.composite.vectors import Vector
        
        # Create Dict[str, Option[List[int]]] codec
        inner_codec = Vector[int]
        middle_codec = Option[list]  # Optional list
        outer_codec = DictionaryCodec(
            str, Optional[list], None, middle_codec
        )
        
        value = {
            "some": [1, 2, 3],
            "none": None,
            "empty": []
        }
        
        encoded = outer_codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value

    @pytest.mark.parametrize("types,expected_error", [
        ((str,), TypeError),         # Missing value type
        ((str, int, bool), TypeError),  # Too many types
        (int, TypeError),           # Not a tuple
        ((list, int), ValueError),  # No codec for raw list
    ])
    def test_invalid_type_specifications(self, types, expected_error):
        """Test handling of invalid type specifications."""
        with pytest.raises(expected_error):
            Dict[types]