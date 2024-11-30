"""
Unit tests for option codec implementation.
"""

from jam.core.codec.composite.arrays import ArrayCodec
import pytest
from typing import Optional, Union
from jam.core.codec.composite.options import (
    Option, OptionCodec, make_option_codec,
    register_option_type, EncodeError, DecodeError
)

class TestOptionCodec:
    """Test suite for option encoding/decoding."""
    
    @pytest.mark.parametrize("type_,value", [
        (int, 42),
        (str, "hello"),
        (bool, True),
        (float, 3.14),
        (bytes, b"data"),
    ])
    def test_some_values(self, type_, value):
        """Test encoding/decoding of present values of different types."""
        codec = OptionCodec(type_)
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)
        assert size == codec.encode_size(value)
        # Check tag byte
        assert encoded[0] == codec.TAG_SOME

    @pytest.mark.parametrize("type_", [int, str, bool, float, bytes])
    def test_none_values(self, type_):
        """Test encoding/decoding of None for different value types."""
        codec = OptionCodec(type_)
        encoded = codec.encode(None)
        decoded, size = codec.decode_from(encoded)
        assert decoded is None
        assert size == 1  # Just tag byte
        assert size == len(encoded)
        assert size == codec.encode_size(None)
        # Check tag byte
        assert encoded[0] == codec.TAG_NONE

    def test_nested_options(self):
        """Test encoding/decoding of nested optional values."""
        # Create Option[Option[int]] codec
        inner_codec = OptionCodec(int)
        outer_codec = OptionCodec(inner_codec)
        
        # Test various nesting combinations
        test_cases = [
            None,           # Outer None
            42,            # Some(Some(42))
            None,          # Some(None)
        ]
        
        for value in test_cases:
            encoded = outer_codec.encode(value)
            decoded, size = outer_codec.decode_from(encoded)
            assert decoded == value
            assert size == len(encoded)

    def test_invalid_types(self):
        """Test handling of invalid value types."""
        codec = Option[int]
        
        invalid_values = [
            "not an int",  # Wrong type
            3.14,          # Float when expecting int
            [],            # List when expecting int
        ]
        
        for value in invalid_values:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = Option[int]
        
        # Test None value with too small buffer
        with pytest.raises(EncodeError):
            codec.encode_into(None, bytearray())
            
        # Test Some value with too small buffer
        value = 42
        size = codec.encode_size(value)
        with pytest.raises(EncodeError):
            codec.encode_into(value, bytearray(size - 1))
            
        # Test decoding from empty buffer
        with pytest.raises(DecodeError):
            codec.decode_from(bytes([]))
            
        # Test decoding Some with truncated value
        encoded = codec.encode(42)
        with pytest.raises(DecodeError):
            codec.decode_from(encoded[:-1])

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        codec = Option[int]
        value = 42
        
        # Calculate buffer size with padding
        size = codec.encode_size(value)
        buffer = bytearray([0xFF] * (size + 2))
        
        # Test encoding at offset
        written = codec.encode_into(value, buffer, 1)
        assert written == size
        
        # Test decoding at offset
        decoded, read = codec.decode_from(buffer, 1)
        assert decoded == value
        assert read == size
        
        # Check padding wasn't overwritten
        assert buffer[0] == 0xFF
        assert buffer[-1] == 0xFF

    def test_invalid_tag(self):
        """Test handling of invalid tag values."""
        codec = Option[int]
        
        # Create buffer with invalid tag
        buffer = bytearray([2])  # Neither TAG_NONE (0) nor TAG_SOME (1)
        
        with pytest.raises(DecodeError) as exc_info:
            codec.decode_from(buffer)
        assert "Invalid option tag" in str(exc_info.value)

    def test_codec_constructors(self):
        """Test different ways of creating option codecs."""
        value = 42
        
        # Using Option type syntax
        codec1 = Option[int]
        
        # Using make_option_codec function
        codec2 = make_option_codec(int)
        
        # Using OptionCodec constructor
        codec3 = OptionCodec(int)
        
        # All should produce identical results
        encoded1 = codec1.encode(value)
        encoded2 = codec2.encode(value)
        encoded3 = codec3.encode(value)
        
        assert encoded1 == encoded2 == encoded3

    def test_registry_integration(self):
        """Test integration with codec registry."""
        from jam.core.codec.base import CodecRegistry
        
        # Register Optional[int] type
        register_option_type(Optional[int])
        
        # Test encoding through registry
        value = 42
        codec = CodecRegistry.get(Optional[int])
        assert codec is not None
        
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value

    @pytest.mark.parametrize("value,expected_size", [
        (None, 1),                # Just tag
        (42, 9),                  # tag + int (8 bytes)
        ("hello", 14),            # tag + len (8 bytes) + "hello"
        (True, 2),                # tag + bool (1 byte)
    ])
    def test_specific_sizes(self, value, expected_size):
        """Test specific encoding sizes for different types and values."""
        type_ = type(value) if value is not None else int
        codec = OptionCodec(type_)
        
        if value is not None:
            encoded = codec.encode(value)
            assert len(encoded) == expected_size
            assert codec.encode_size(value) == expected_size
        else:
            encoded = codec.encode(None)
            assert len(encoded) == 1
            assert codec.encode_size(None) == 1

    def test_complex_value_types(self):
        """Test option codec with complex value types."""
        # Test with list of integers
        from jam.core.codec.composite.arrays import Array
        inner_codec = ArrayCodec(int, 3)
        codec = OptionCodec(list, inner_codec)
        
        value = [1, 2, 3]
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert codec.decode_from(codec.encode(None))[0] is None

    def test_option_type_errors(self):
        """Test error handling in Option type construction."""
        # Missing type argument
        with pytest.raises(TypeError):
            Option[int]
            
        # Too many type arguments
        with pytest.raises(TypeError):
            Option[int]

    def test_encode_decode_empty_string(self):
        """Test handling of empty string as Some value."""
        codec = OptionCodec(str)
        value = ""
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)
        assert encoded[0] == codec.TAG_SOME

    def test_partial_decode_failure(self):
        """Test handling of decode failures in Some values."""
        codec = OptionCodec(int)
        
        # Create valid encoding and corrupt it
        encoded = codec.encode(42)
        corrupted = encoded[:-1]  # Remove last byte
        
        with pytest.raises(DecodeError) as exc_info:
            codec.decode_from(corrupted)
        assert "Failed to decode Some value" in str(exc_info.value)