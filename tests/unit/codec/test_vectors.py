"""
Unit tests for vector codec implementation.
"""

import pytest
from typing import List, Sequence, Union
from jam.types.base.boolean import Boolean
from jam.types.base.integers import Int
from jam.types.base.string import String
from jam.utils.codec.composite.vectors import VectorCodec
from jam.utils.codec.base import EncodeError, DecodeError
from jam.types.base.vector import Vector

class TestVectorCodec:
    """Test suite for vector encoding/decoding."""

    def test_basic_vector(self):
        """Test basic encoding/decoding of integer vectors."""
        codec = VectorCodec()
        value = Vector([Int(1), Int(2), Int(3)])

        encoded = value.encode()
        decoded, size = Vector.decode_from(Int, encoded)
        assert decoded == value
        assert size == len(encoded)

    @pytest.mark.parametrize("value,expected_prefix", [
        (Vector([]), bytes([0])),                   
        (Vector([Int(1)]), bytes([1])),             
        (Vector([Int(1), Int(2)]), bytes([2])),     
        (Vector([Int(1)] * 126), bytes([126])),    
        (Vector([Int(1)] * 200), bytes([128])),       
    ])
    def test_length_prefixes(self, value, expected_prefix):
        """Test that length prefixes are correctly encoded."""
        encoded = value.encode()
        assert encoded[:len(expected_prefix)] == expected_prefix

    @pytest.mark.parametrize("values", [
        ([Int(1), Int(2), Int(3), Int(4), Int(5)]),
        ([Boolean(True), Boolean(False), Boolean(True)]),
        ([String("hello"), String("world")]),
    ])
    def test_various_types(self, values):
        """Test vector codec with various element types."""
        value = Vector(values)
        encoded = value.encode()
        decoded, size = Vector.decode_from(type(values[0]), encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_nested_vectors(self):
        """Test encoding/decoding of nested vectors."""
        class IntVector(Vector[Int]):
            @staticmethod
            def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> tuple[Sequence[Int], int]:
                return Vector.decode_from(Int, buffer, offset)
        
        vec1 = IntVector([Int(1), Int(2)])
        vec2 = IntVector([Int(3), Int(4)])
        vec3 = IntVector([Int(6), Int(7)])
        value = Vector([vec1, vec2, vec3])
        encoded = value.encode()
        print(encoded, value)
        decoded, size = Vector.decode_from(IntVector, encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        value = Vector([Int(1), Int(2), Int(3)])
        
        # Test decoding from too small buffer
        encoded = value.encode()
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                Vector.decode_from(Int, encoded[:i])

    def test_invalid_element_types(self):
        """Test handling of invalid element types."""
        codec = VectorCodec()
        
        invalid_lists = [
            Vector([Int(1), String("not int"), Int(3)]),
            Vector([Int(1), Int(2), None]),
            Vector([Int(1), Int(2), Boolean(True)]),
        ]
        
        for value in invalid_lists:
            with pytest.raises(EncodeError):
                value.encode()

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        codec = VectorCodec()
        value = Vector([Int(1), Int(2), Int(3)])
        
        # Create buffer with padding
        buffer = bytearray([0xFF] * (codec.encode_size(value) + 2))
        
        # Test encoding at offset
        written = codec.encode_into(value, buffer, 1)
        
        # Test decoding at offset
        decoded, size = Vector.decode_from(Int, buffer, 1)
        assert decoded == value
        assert size == written
        
        # Verify padding wasn't overwritten
        assert buffer[0] == 0xFF
        assert buffer[-1] == 0xFF

    def test_empty_vector(self):
        """Test handling of empty vectors."""
        codec = VectorCodec()
        value = Vector([])
        
        encoded = codec.encode(value)
        # Should just be length byte (0)
        assert encoded == bytes([0])
        
        decoded, size = Vector.decode_from(Int, encoded)
        assert decoded == value
        assert size == 1

    def test_partial_decode_failure(self):
        """Test handling of decode failures partway through vector."""
        codec = VectorCodec()
        
        # Create valid encoding and corrupt it
        valid = codec.encode([Int(1), Int(2), Int(3)])
        corrupted = valid[:-1]  # Remove last byte
        
        with pytest.raises(DecodeError):
            Vector.decode_from(Int, corrupted)
