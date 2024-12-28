"""
Unit tests for option codec implementation.
"""

import pytest
from typing import Optional
from jam.utils.codec.composite.options import OptionCodec
from jam.utils.codec.base import EncodeError, DecodeError
from jam.utils.codec.primitives.integers import IntegerCodec, GeneralCodec
from jam.utils.codec.primitives.strings import StringCodec
from jam.utils.codec.primitives.bools import BooleanCodec

class TestOptionCodec:
    """Test suite for option encoding/decoding."""

    def test_none_value(self):
        """Test encoding/decoding of None values."""
        codec = OptionCodec(int, general_codec)
        value = None
        encoded = codec.encode(value)
        # Should just be tag byte (0)
        assert encoded == bytes([0])
        decoded, size = codec.decode_from(encoded)
        assert decoded is None
        assert size == 1

    def test_some_value(self):
        """Test encoding/decoding of Some values."""
        codec = OptionCodec(int, general_codec)
        value = 42
        encoded = codec.encode(value)
        # Should be tag byte (1) followed by encoded value
        assert encoded[0] == 1
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    @pytest.mark.parametrize("value_type,codec,sample", [
        (int, general_codec, 42),
        (str, string_codec, "hello"),
        (bool, boolean_codec, True),
    ])
    def test_various_types(self, value_type, codec, sample):
        """Test option codec with various value types."""
        option_codec = OptionCodec(value_type, codec)
        
        # Test Some case
        encoded = option_codec.encode(sample)
        decoded, size = option_codec.decode_from(encoded)
        assert decoded == sample
        assert size == len(encoded)
        
        # Test None case
        encoded = option_codec.encode(None)
        decoded, size = option_codec.decode_from(encoded)
        assert decoded is None
        assert size == 1

    def test_nested_options(self):
        """Test encoding/decoding of nested options."""
        inner_codec = OptionCodec(int, general_codec)
        outer_codec = OptionCodec(type(Optional[int]), inner_codec)
        
        test_values = [
            None,               # Outer None
            42,                # Some(Some(42))
        ]
        
        for value in test_values:
            encoded = outer_codec.encode(value)
            decoded, size = outer_codec.decode_from(encoded)
            assert decoded == value
            assert size == len(encoded)

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = OptionCodec(int, general_codec)
        value = 42
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
        codec = OptionCodec(int, general_codec)
        
        invalid_values = [
            "not an int",    # str
            3.14,            # float
            [1, 2, 3],      # list
            {1, 2, 3},      # set
        ]
        
        for value in invalid_values:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        codec = OptionCodec(int, general_codec)
        value = 42
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

    def test_invalid_tag(self):
        """Test handling of invalid tag values during decoding."""
        codec = OptionCodec(int, general_codec)
        
        # Create buffer with invalid tag
        invalid_tag = 2
        buffer = bytes([invalid_tag])
        
        with pytest.raises(DecodeError) as exc_info:
            codec.decode_from(buffer)
        assert "Invalid option tag" in str(exc_info.value)

    def test_complex_nested_structure(self):
        """Test complex nested option structures."""
        from jam.utils.codec.composite.vectors import VectorCodec
        
        # Create Option[Vector[Option[int]]] codec
        inner_codec = OptionCodec(int, general_codec)
        middle_codec = VectorCodec(inner_codec)
        outer_codec = OptionCodec(list, middle_codec)
        
        test_values = [
            None,                           # None
            [None, 1, None, 2, 3],         # Some([None, Some(1), None, Some(2), Some(3)])
            [],                            # Some([])
        ]
        
        for value in test_values:
            encoded = outer_codec.encode(value)
            decoded, size = outer_codec.decode_from(encoded)
            assert decoded == value
            assert size == len(encoded)

    def test_string_options(self):
        """Test options with string values of various content."""
        codec = OptionCodec(str, string_codec)
        test_values = [
            None,               # None
            "",                # Empty string
            "hello",           # ASCII
            "Hello, 世界！",    # Mixed ASCII and Unicode
            "🦀 Rust",         # Emojis
            "a" * 1000,        # Long string
        ]
        
        for value in test_values:
            encoded = codec.encode(value)
            decoded, size = codec.decode_from(encoded)
            assert decoded == value
            assert size == len(encoded)

    def test_partial_decode_failure(self):
        """Test handling of decode failures partway through value."""
        codec = OptionCodec(int, general_codec)
        
        # Create valid encoding and corrupt it
        valid = codec.encode(42)
        corrupted = valid[:-1]  # Remove last byte
        
        with pytest.raises(DecodeError) as exc_info:
            codec.decode_from(corrupted)
        assert "Failed to decode Some value" in str(exc_info.value) 