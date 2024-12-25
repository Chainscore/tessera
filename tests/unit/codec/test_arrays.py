"""
Unit tests for array codec implementation.
"""

import pytest
from typing import List, Sequence
from jam.utils.codec.composite.arrays import ArrayCodec
from jam.utils.codec.base import EncodeError, DecodeError
from jam.utils.codec.primitives.integers import general_codec
from jam.utils.codec.primitives.bools import boolean_codec
from jam.utils.codec.primitives.strings import string_codec

class TestArrayCodec:
    """Test suite for array encoding/decoding."""

    def test_basic_integer_array(self):
        """Test basic encoding/decoding of integer arrays."""
        codec = ArrayCodec(3, general_codec)
        value = [1, 2, 3]

        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_nested_arrays(self):
        """Test encoding/decoding of nested arrays."""
        inner_codec = ArrayCodec(3, general_codec)
        outer_codec = ArrayCodec(2, inner_codec)
        
        value = [[1, 2, 3], [4, 5, 6]]
        
        encoded = outer_codec.encode(value)
        decoded, size = outer_codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    @pytest.mark.parametrize("codec,values", [
        (ArrayCodec(3, general_codec), [1, 2, 3]),
        (ArrayCodec(2, boolean_codec), [True, False]),
        (ArrayCodec(2, string_codec), ["hello", "world"]),
    ])
    def test_various_types(self, codec, values):
        """Test array codec with various element types."""
        encoded = codec.encode(values)
        decoded, size = codec.decode_from(encoded)
        assert decoded == values
        assert size == len(encoded)

    def test_empty_array(self):
        """Test handling of zero-length arrays."""
        codec = ArrayCodec(0, general_codec)
        value = []
        
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_maximum_size(self):
        """Test array size limits."""
        # Test maximum allowed size
        codec = ArrayCodec(1000, general_codec)
        assert codec.length == 1000

        # Test exceeding maximum size
        with pytest.raises(ValueError):
            ArrayCodec(1001, general_codec)

    def test_negative_length(self):
        """Test that negative lengths are rejected."""
        with pytest.raises(ValueError):
            ArrayCodec(-1, general_codec)

    def test_length_mismatch(self):
        """Test handling of incorrect array lengths."""
        codec = ArrayCodec(3, general_codec)
        
        # Too few elements
        with pytest.raises(EncodeError):
            codec.encode([1, 2])
            
        # Too many elements
        with pytest.raises(EncodeError):
            codec.encode([1, 2, 3, 4])

    def test_invalid_element_type(self):
        """Test handling of invalid element types during encoding."""
        codec = ArrayCodec(3, general_codec)
        
        with pytest.raises(EncodeError):
            codec.encode(["not", "an", "int"])

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = ArrayCodec(3, general_codec)
        value = [1, 2, 3]
        
        encoded = codec.encode(value)
        # Test decoding from too small buffer
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                codec.decode_from(encoded[:i])

    def test_complex_nested_structure(self):
        """Test complex nested array structures."""
        # Create 2x2x2 array of integers
        inner_codec = ArrayCodec(2, general_codec)
        middle_codec = ArrayCodec(2, inner_codec)
        outer_codec = ArrayCodec(2, middle_codec)
        
        value = [[[1, 2], [1, 2]], [[1, 2], [1, 2]]]
        
        encoded = outer_codec.encode(value)
        decoded, size = outer_codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)