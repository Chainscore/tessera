"""
Unit tests for vector codec implementation.
"""

from codecs import encode, decode
import pytest
from typing import List, Optional, Sequence
from jam.core.codec.composite.vectors import (
    Vector, VectorCodec, make_vector_codec, register_vector_type,
    EncodeError, DecodeError
)

class TestVectorCodec:
    """Test suite for vector encoding/decoding."""

    def test_empty_vector(self):
        """Test encoding/decoding of empty vectors."""
        codec = Vector[int]
        value = []
        encoded = encode(value)
        # Should just be length byte (0)
        assert encoded == bytes([0])
        decoded, size = decode(encoded)
        assert decoded == value
        assert size == 1

    @pytest.mark.parametrize("length", [
        0xFC,    # Maximum single-byte length
        0xFD,    # Start of two-byte length
        0xFF,    # Edge within two-byte length
        0xFFFF,  # Maximum two-byte length
        0x10000, # Start of three-byte length
    ])
    def test_length_encoding_boundaries(self, length):
        """Test vector encoding at length boundaries."""
        codec = VectorCodec(int)
        value = [0] * length
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert len(decoded) == length
        assert decoded == value

    @pytest.mark.parametrize("value,expected_prefix", [
        ([], bytes([0])),  # Empty list
        ([1], bytes([1])),  # Single element
        ([1, 2], bytes([2])),  # Two elements
        ([1] * 0xFC, bytes([0xFC])),  # Max single byte
        ([1] * 0xFD, bytes([0xFF, 0xFD, 0x00])),  # Min two byte
        ([1] * 0xFFFF, bytes([0xFF, 0xFF, 0xFF])),  # Max two byte
    ])
    def test_length_prefixes(self, value, expected_prefix):
        """Test that length prefixes are correctly encoded."""
        codec = VectorCodec(int)
        encoded = codec.encode(value)
        assert encoded[:len(expected_prefix)] == expected_prefix

    @pytest.mark.parametrize("type_,values", [
        (int, [1, 2, 3, 4, 5]),
        (str, ["hello", "world"]),
        (bool, [True, False, True]),
        (float, [1.0, 2.5, 3.14]),
    ])
    def test_various_types(self, type_, values):
        """Test vector codec with various element types."""
        codec = VectorCodec(type_)
        encoded = codec.encode(values)
        decoded, size = codec.decode_from(encoded)
        assert decoded == values
        assert size == len(encoded)

    def test_nested_vectors(self):
        """Test encoding/decoding of nested vectors."""
        codec = VectorCodec(int)

        # Create Vector[Vector[int]] codec
        inner_codec = VectorCodec(int)
        outer_codec = VectorCodec(list, inner_codec)
        
        value = [[1, 2], [3, 4, 5], [6]]
        encoded = outer_codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = VectorCodec(int)
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

    def test_invalid_types(self):
        """Test handling of invalid value types."""
        codec = VectorCodec(int)
        
        invalid_values = [
            42,              # int
            "not a list",    # str
            {1, 2, 3},       # set
            (1, 2, 3),       # tuple
            None,            # None
        ]
        
        for value in invalid_values:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_invalid_element_types(self):
        """Test handling of invalid element types."""
        codec = VectorCodec(int)
        
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
        codec = VectorCodec(int)
        value = [1, 2, 3]
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

    def test_vector_constructors(self):
        """Test different ways of creating vector codecs."""
        value = [1, 2, 3]
        
        # Using Vector type syntax
        codec1 = VectorCodec(int)
        
        # Using make_vector_codec function
        codec2 = make_vector_codec(int)
        
        # Using VectorCodec constructor
        codec3 = VectorCodec(int)
        
        # All should produce identical results
        encoded1 = codec1.encode(value)
        encoded2 = codec2.encode(value)
        encoded3 = codec3.encode(value)
        
        assert encoded1 == encoded2 == encoded3

    def test_registry_integration(self):
        """Test integration with codec registry."""
        from jam.core.codec.base import CodecRegistry
        
        # Register vector type
        vector_type = List[int]
        register_vector_type(vector_type)
        
        # Test encoding through registry
        value = [1, 2, 3]
        codec = CodecRegistry.get(vector_type)
        assert codec is not None
        
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value

    def test_string_vectors(self):
        """Test vectors of strings with various content."""
        codec = VectorCodec(str)
        test_values = [
            [],                 # Empty
            [""],              # Empty string
            ["hello"],         # Single ASCII
            ["hello", ""],     # Mixed with empty
            ["🦀", "Rust"],    # Unicode
            ["a" * 1000],      # Long string
        ]
        
        for value in test_values:
            encoded = codec.encode(value)
            decoded, size = codec.decode_from(encoded)
            assert decoded == value
            assert size == len(encoded)

    def test_complex_nested_structure(self):
        """Test complex nested vector structures."""
        from jam.core.codec.composite.options import Option
        
        # Create Vector[Option[Vector[int]]] codec
        codec = VectorCodec(int)
        inner_codec = VectorCodec(int)
        middle_codec = Option[List[int]]
        outer_codec = VectorCodec(middle_codec)
        
        value = [
            [1, 2, 3],
            None,
            [4, 5],
            None,
            []
        ]
        
        encoded = outer_codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_partial_decode_failure(self):
        """Test handling of decode failures partway through vector."""
        codec = VectorCodec(int)
        
        # Create valid encoding and corrupt it
        valid = codec.encode([1, 2, 3])
        corrupted = valid[:-1]  # Remove last byte
        
        with pytest.raises(DecodeError) as exc_info:
            codec.decode_from(corrupted)
        assert "Failed to decode vector element" in str(exc_info.value)

    def test_very_large_vector(self):
        """Test handling of vectors approaching size limits."""
        codec = VectorCodec(int)
        
        # Test with a large but valid size
        large_size = 0xFFFF  # 65535 elements
        value = [0] * large_size
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert len(decoded) == large_size
        
        # Test with size too large
        too_large = 0x1_0000_0000  # > u32::MAX
        with pytest.raises(EncodeError):
            codec.encode([0] * too_large)

    def test_invalid_length_tag(self):
        """Test handling of invalid length tags during decoding."""
        codec = VectorCodec(int)
        
        # Create buffer with invalid tag
        invalid_buffer = bytes([0xFC + 1])  # Invalid tag (not 0xFD, 0xFE, or 0xFF)
        
        with pytest.raises(DecodeError) as exc_info:
            codec.decode_from(invalid_buffer)
        assert "Invalid length tag" in str(exc_info.value)