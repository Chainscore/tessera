"""
Unit tests for dictionary codec implementation.
"""

import pytest
from typing import Dict, Mapping
from jam.types.base.boolean import Boolean
from jam.types.base.integers import Int
from jam.types.base.string import String
from jam.utils.codec.composite.dictionaries import DictionaryCodec
from jam.utils.codec.base import Codable, EncodeError, DecodeError
from jam.utils.codec.primitives.integers import GeneralCodec, IntegerCodec
from jam.utils.codec.primitives.strings import StringCodec
from jam.utils.codec.primitives.bools import BooleanCodec

class TestDictionaryCodec:
    """Test suite for dictionary encoding/decoding."""

    def test_empty_dict(self):
        """Test encoding/decoding of empty dictionaries."""
        codec = DictionaryCodec()
        value = {}
        encoded = codec.encode(value)
        # Should just be length byte (0)
        assert encoded == bytes([0])
        decoded, size = codec.decode_from(Codable, Codable, encoded)
        assert decoded == value
        assert size == 1


    @pytest.mark.parametrize("key_type,value_type,sample", [
        (String, Int, {String("a"): Int(1), String("b"): Int(2)}),
        (Int, Boolean, {Int(1): Boolean(True), Int(2): Boolean(False)}),
        (String, String, {String("hello"): String("world")}),
    ])
    def test_various_types(self, key_type: type, value_type: type, sample: dict):
        """Test dictionary codec with various key/value types."""
        codec = DictionaryCodec()
        encoded = codec.encode(sample)
        decoded, size = DictionaryCodec.decode_from(key_type, value_type, encoded)
        assert decoded == sample
        assert size == len(encoded)

    # def test_nested_dictionaries(self):
    #     """Test encoding/decoding of nested dictionaries."""
    #     inner_codec = DictionaryCodec(str, int, string_codec, general_codec)
    #     outer_codec = DictionaryCodec(str, dict, string_codec, inner_codec)
        
    #     value = {
    #         "first": {"a": 1, "b": 2},
    #         "second": {"c": 3, "d": 4}
    #     }
        
    #     encoded = outer_codec.encode(value)
    #     decoded, size = outer_codec.decode_from(encoded)
    #     assert decoded == value
    #     assert size == len(encoded)

    def test_deterministic_encoding(self):
        """Test that dictionary encoding is deterministic (same dict = same bytes)."""
        codec = DictionaryCodec()
        dict1 = {String("b"): Int(2), String("a"): Int(1), String("c"): Int(3)}
        dict2 = {String("a"): Int(1), String("c"): Int(3), String("b"): Int(2)}
        
        encoded1 = codec.encode(dict1)
        encoded2 = codec.encode(dict2)
        assert encoded1 == encoded2

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = DictionaryCodec()
        value = {String("a"): Int(1), String("b"): Int(2)}
        size = codec.encode_size(value)  # type: ignore
        
        # Test encoding into too small buffer
        with pytest.raises(EncodeError):
            codec.encode_into(value, bytearray(size - 1))  # type: ignore
        
        # Test decoding from too small buffer
        encoded = codec.encode(value)
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                codec.decode_from(String, Int, encoded[:i])

    def test_invalid_types(self):
        """Test handling of invalid value types."""
        codec = DictionaryCodec()
        
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
        codec = DictionaryCodec()
        
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
        codec = DictionaryCodec()
        value = {String("a"): Int(1), String("b"): Int(2)} 
        size = codec.encode_size(value)  # type: ignore
        
        # Create buffer with padding
        buffer = bytearray([0xFF] * (size + 2))
        
        # Test encoding at offset
        written = codec.encode_into(value, buffer, 1)  # type: ignore
        assert written == size
        
        # Test decoding at offset
        decoded, read = codec.decode_from(String, Int, buffer, 1)
        assert decoded == value
        assert read == size
        
        # Verify padding wasn't overwritten
        assert buffer[0] == 0xFF
        assert buffer[-1] == 0xFF

    def test_string_key_values(self):
        """Test dictionaries with string keys and values with various content."""
        codec = DictionaryCodec()
        test_values = {
            String(""): String(""),                    # Empty strings
            String("hello"): String("world"),          # ASCII
            String("🦀"): String("Rust"),              # Unicode
            String("key"): String("a" * 1000),         # Long string
            String("unicode"): String("Hello, 世界！")  # Mixed ASCII and Unicode
        }
        
        encoded = codec.encode(test_values)
        decoded, size = codec.decode_from(String, String, encoded)
        assert decoded == test_values
        assert size == len(encoded)

    # def test_complex_nested_structure(self):
    #     """Test complex nested dictionary structures."""
    #     from jam.utils.codec.composite.vectors import VectorCodec
        
    #     # Create Dict[str, Dict[str, List[int]]] codec
    #     inner_list_codec = VectorCodec()
    #     inner_dict_codec = DictionaryCodec()
    #     outer_codec = DictionaryCodec()
        
    #     value = {
    #         "first": {
    #             "a": [1, 2, 3],
    #             "b": []
    #         },
    #         "second": {
    #             "c": [4, 5]
    #         }
    #     }
        
    #     encoded = outer_codec.encode(value)
    #     decoded, size = outer_codec.decode_from(encoded)
    #     assert decoded == value
    #     assert size == len(encoded) 