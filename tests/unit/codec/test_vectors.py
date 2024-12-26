"""
Unit tests for vector codec implementation.
"""

import pytest
from typing import List, Sequence
from jam.utils.codec.composite.vectors import VectorCodec
from jam.utils.codec.base import EncodeError, DecodeError
from jam.utils.codec.primitives.integers import general_codec
from jam.utils.codec.primitives.bools import boolean_codec
from jam.utils.codec.primitives.strings import string_codec

class TestVectorCodec:
    """Test suite for vector encoding/decoding."""

    def test_basic_vector(self):
        """Test basic encoding/decoding of integer vectors."""
        codec = VectorCodec(general_codec)
        value = [1, 2, 3]

        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    @pytest.mark.parametrize("length", [
        0,      # Empty vector
        0xFC,   # Maximum direct length
        0xFD,   # Minimum 2-byte length
        0xFF,   # Middle 2-byte length
        0xFFFF, # Maximum 2-byte length
    ])
    def test_length_boundaries(self, length):
        """Test vector encoding at length boundaries."""
        codec = VectorCodec(general_codec)
        value = [0] * length
        
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert len(decoded) == length
        assert decoded == value

    @pytest.mark.parametrize("value,expected_prefix", [
        ([], bytes([0])),                    # Empty vector
        ([1], bytes([1])),                   # Single element
        ([1, 2], bytes([2])),               # Two elements
        ([1] * 0xFC, bytes([0xFC])),        # Max direct length
        ([1] * 0xFD, bytes([0xFF, 0xFD, 0x00])),  # Min 2-byte length
    ])
    def test_length_prefixes(self, value, expected_prefix):
        """Test that length prefixes are correctly encoded."""
        codec = VectorCodec(general_codec)
        encoded = codec.encode(value)
        assert encoded[:len(expected_prefix)] == expected_prefix

    @pytest.mark.parametrize("element_type,codec,values", [
        (int, general_codec, [1, 2, 3, 4, 5]),
        (bool, boolean_codec, [True, False, True]),
        (str, string_codec, ["hello", "world"]),
    ])
    def test_various_types(self, element_type, codec, values):
        """Test vector codec with various element types."""
        vector_codec = VectorCodec(codec)
        encoded = vector_codec.encode(values)
        decoded, size = vector_codec.decode_from(encoded)
        assert decoded == values
        assert size == len(encoded)

    def test_nested_vectors(self):
        """Test encoding/decoding of nested vectors."""
        inner_codec = VectorCodec(general_codec)
        outer_codec = VectorCodec(inner_codec)
        
        value = [[1, 2], [3, 4, 5], [6]]
        encoded = outer_codec.encode(value)
        decoded, size = outer_codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = VectorCodec(general_codec)
        value = [1, 2, 3]
        
        # Test decoding from too small buffer
        encoded = codec.encode(value)
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                codec.decode_from(encoded[:i])

    def test_invalid_types(self):
        """Test handling of invalid value types."""
        codec = VectorCodec(general_codec)
        
        invalid_values = [
            42,           # int
            "not a list", # str
            {1, 2, 3},   # set
            None,        # None
        ]
        
        for value in invalid_values:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_invalid_element_types(self):
        """Test handling of invalid element types."""
        codec = VectorCodec(general_codec)
        
        invalid_lists = [
            ["not int"],
            [1, "not int", 3],
            [1, 2, None],
            [1, 2, 3.14],
        ]
        
        for value in invalid_lists:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        codec = VectorCodec(general_codec)
        value = [1, 2, 3]
        
        # Create buffer with padding
        buffer = bytearray([0xFF] * (codec.encode_size(value) + 2))
        
        # Test encoding at offset
        written = codec.encode_into(value, buffer, 1)
        
        # Test decoding at offset
        decoded, size = codec.decode_from(buffer, 1)
        assert decoded == value
        assert size == written
        
        # Verify padding wasn't overwritten
        assert buffer[0] == 0xFF
        assert buffer[-1] == 0xFF

    def test_empty_vector(self):
        """Test handling of empty vectors."""
        codec = VectorCodec(general_codec)
        value = []
        
        encoded = codec.encode(value)
        # Should just be length byte (0)
        assert encoded == bytes([0])
        
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == 1

    def test_partial_decode_failure(self):
        """Test handling of decode failures partway through vector."""
        codec = VectorCodec(general_codec)
        
        # Create valid encoding and corrupt it
        valid = codec.encode([1, 2, 3])
        corrupted = valid[:-1]  # Remove last byte
        
        with pytest.raises(DecodeError):
            codec.decode_from(corrupted)