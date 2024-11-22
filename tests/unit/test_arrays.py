"""
Unit tests for array codec implementation.
"""

import pytest
from typing import List, Sequence
from jam.core.codec.composite.arrays import (
    Array, ArrayCodec, make_array_codec,
    EncodeError, DecodeError
)

class TestArrayCodec:
    """Test suite for array encoding/decoding."""

    def test_basic_integer_array(self):
        """Test basic encoding/decoding of integer arrays."""
        codec = Array[int, 3]
        value = [1, 2, 3]
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_nested_arrays(self):
        """Test encoding/decoding of nested arrays."""
        # Create a 2x3 array codec
        inner_codec = Array[int, 3]
        outer_codec = ArrayCodec(Sequence[int], 2, inner_codec)
        
        value = [[1, 2, 3], [4, 5, 6]]
        encoded = outer_codec.encode(value)
        decoded, size = outer_codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    @pytest.mark.parametrize("type_,length,values", [
        (int, 3, [1, 2, 3]),
        (bool, 2, [True, False]),
        (str, 2, ["hello", "world"]),
        (float, 4, [1.0, 2.0, 3.0, 4.0]),
    ])
    def test_various_types(self, type_, length, values):
        """Test array codec with various element types."""
        codec = Array[type_, length]
        encoded = codec.encode(values)
        decoded, size = codec.decode_from(encoded)
        assert decoded == values
        assert size == len(encoded)

    def test_empty_array(self):
        """Test handling of zero-length arrays."""
        codec = Array[int, 0]
        encoded = codec.encode([])
        decoded, size = codec.decode_from(encoded)
        assert decoded == []
        assert size == 0

    def test_maximum_size(self):
        """Test array size limits."""
        # Test maximum allowed size
        codec = Array[int, 1000]
        assert codec.length == 1000

        # Test exceeding maximum size
        with pytest.raises(ValueError):
            Array[int, 1001]

    def test_negative_length(self):
        """Test that negative lengths are rejected."""
        with pytest.raises(ValueError):
            Array[int, -1]

    def test_length_mismatch(self):
        """Test handling of incorrect array lengths."""
        codec = Array[int, 3]
        
        # Too few elements
        with pytest.raises(EncodeError):
            codec.encode([1, 2])
            
        # Too many elements
        with pytest.raises(EncodeError):
            codec.encode([1, 2, 3, 4])

    def test_invalid_element_type(self):
        """Test handling of invalid element types during encoding."""
        codec = Array[int, 3]
        
        # Wrong element type
        with pytest.raises(EncodeError):
            codec.encode(["not", "an", "int"])

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = Array[int, 3]
        value = [1, 2, 3]
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
        codec = Array[int, 3]
        value = [1, 2, 3]
        buffer_size = codec.encode_size(value)
        
        # Create buffer with padding
        buffer = bytearray([0xFF] * (buffer_size + 2))
        
        # Test encoding at offset
        written = codec.encode_into(value, buffer, 1)
        assert written == buffer_size
        
        # Test decoding at offset
        decoded, size = codec.decode_from(buffer, 1)
        assert decoded == value
        assert size == buffer_size
        
        # Verify padding wasn't overwritten
        assert buffer[0] == 0xFF
        assert buffer[-1] == 0xFF

    def test_array_constructor_methods(self):
        """Test different ways of creating array codecs."""
        value = [1, 2, 3]
        
        # Using Array type syntax
        codec1 = Array[int, 3]
        
        # Using make_array_codec function
        codec2 = make_array_codec(int, 3)
        
        # Using ArrayCodec constructor
        codec3 = ArrayCodec(int, 3)
        
        # All should produce identical results
        encoded1 = codec1.encode(value)
        encoded2 = codec2.encode(value)
        encoded3 = codec3.encode(value)
        
        assert encoded1 == encoded2 == encoded3

    @pytest.mark.parametrize("length,values", [
        (2, ["hello", "world"]),  # Basic strings
        (3, ["", "mid", "long" * 100]),  # Various lengths
        (2, ["Hello, 世界", "🦀 Rust"]),  # Unicode
    ])
    def test_string_arrays(self, length, values):
        """Test arrays of strings with various content."""
        codec = Array[str, length]
        encoded = codec.encode(values)
        decoded, size = codec.decode_from(encoded)
        assert decoded == values
        assert size == len(encoded)

    def test_array_type_validation(self):
        """Test type validation in Array type constructor."""
        # Invalid length type
        with pytest.raises(TypeError):
            Array[int, "3"]
            
        # Missing length
        with pytest.raises(TypeError):
            Array[int]
            
        # Too many parameters
        with pytest.raises(TypeError):
            Array[int, 3, "extra"]

    def test_complex_nested_structure(self):
        """Test complex nested array structures."""
        # Create 2x2x2 array of integers
        inner_codec = Array[int, 2]
        middle_codec = ArrayCodec(Sequence[int], 2, inner_codec)
        outer_codec = ArrayCodec(Sequence[Sequence[int]], 2, middle_codec)
        
        value = [
            [[1, 2], [3, 4]],
            [[5, 6], [7, 8]]
        ]
        
        encoded = outer_codec.encode(value)
        decoded, size = outer_codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_partial_decode_failure(self):
        """Test handling of decode failures partway through array."""
        codec = Array[int, 3]
        
        # Create valid encoding and corrupt it
        valid = codec.encode([1, 2, 3])
        corrupted = valid[:len(valid)-1]  # Remove last byte
        
        with pytest.raises(DecodeError) as exc_info:
            codec.decode_from(corrupted)
        assert "Failed to decode array element" in str(exc_info.value)