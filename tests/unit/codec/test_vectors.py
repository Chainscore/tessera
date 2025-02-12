"""
Unit tests for vector codec implementation.
"""

import pytest
from jam.types.base.boolean import Boolean
from jam.types.base.integers import Int
from jam.types.base.string import String
from jam.utils.codec import DecodeError
from jam.types.base import Vector, decodable_vector

@decodable_vector(Int)
class TestIntVector(Vector[Int]): ...

@decodable_vector(TestIntVector)
class TestIntVectorVector(Vector[TestIntVector]): ...

@decodable_vector(Boolean)
class TestBooleanVector(Vector[Boolean]): ...

@decodable_vector(String)
class TestStringVector(Vector[String]): ...

class TestVectorCodec:
    """Test suite for vector encoding/decoding."""

    def test_basic_vector(self):
        """Test basic encoding/decoding of integer vectors."""
        value = TestIntVector([Int(1), Int(2), Int(3)])
        encoded = value.encode()
        decoded, size = TestIntVector.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    @pytest.mark.parametrize("value,expected_prefix", [
        (TestIntVector([]), bytes([0])),                   
        (TestIntVector([Int(1)]), bytes([1])),             
        (TestIntVector([Int(1), Int(2)]), bytes([2])),     
        (TestIntVector([Int(1)] * 126), bytes([126])),    
        (TestIntVector([Int(1)] * 200), bytes([128])),       
    ])
    def test_length_prefixes(self, value, expected_prefix):
        """Test that length prefixes are correctly encoded."""
        encoded = value.encode()
        assert encoded[:len(expected_prefix)] == expected_prefix

    @pytest.mark.parametrize("values", [
        (TestIntVector([Int(1), Int(2), Int(3), Int(4), Int(5)])),
        (TestBooleanVector([Boolean(True), Boolean(False), Boolean(True)])),
        (TestStringVector([String("hello"), String("world")])),
    ])
    def test_various_types(self, values):
        """Test vector codec with various element types."""
        encoded = values.encode()
        decoded, size = values.decode_from(encoded)
        assert decoded == values
        assert size == len(encoded)

    def test_nested_vectors(self):
        """Test encoding/decoding of nested vectors."""
        
        vec1 = TestIntVector([Int(1), Int(2)])
        vec2 = TestIntVector([Int(3), Int(4)])
        vec3 = TestIntVector([Int(6), Int(7)])
        value = TestIntVectorVector([vec1, vec2, vec3])
        encoded = value.encode()
        print(encoded, value)
        decoded, size = TestIntVectorVector.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        value = TestIntVector([Int(1), Int(2), Int(3)])
        
        # Test decoding from too small buffer
        encoded = value.encode()
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                TestIntVector.decode_from(encoded[:i])

    def test_invalid_element_types(self):
        """Test handling of invalid element types."""
        invalid_lists = [
            [Int(1), String("not int"), Int(3)],  # type: ignore
            [Int(1), Int(2), None], # type: ignore
            [Int(1), Int(2), Boolean(True)], # type: ignore
        ]
        
        for value in invalid_lists:
            with pytest.raises(TypeError):
                TestIntVector(value)

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        value = TestIntVector([Int(1), Int(2), Int(3)])
        buffer = bytearray([0xFF] * (value.encode_size() + 2))
        
        # Test encoding at offset
        written = value.encode_into(buffer, 1)
        
        # Test decoding at offset
        decoded, size = TestIntVector.decode_from(buffer, 1)
        assert decoded == value
        assert size == written
        
        # Verify padding wasn't overwritten
        assert buffer[0] == 0xFF
        assert buffer[-1] == 0xFF

    def test_empty_vector(self):
        """Test handling of empty vectors."""
        value = TestIntVector([])
        
        encoded = value.encode()
        # Should just be length byte (0)
        assert encoded == bytes([0])
        
        decoded, size = TestIntVector.decode_from(encoded)
        assert decoded == value
        assert size == 1

    def test_partial_decode_failure(self):
        """Test handling of decode failures partway through vector."""
        value = TestIntVector([Int(1), Int(2), Int(3)])
        
        # Create valid encoding and corrupt it
        valid = value.encode()
        corrupted = valid[:-1]  # Remove last byte
        
        with pytest.raises(DecodeError):
            TestIntVector.decode_from(corrupted)
