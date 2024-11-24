"""
Test composite type system for JAM protocol.
"""

import pytest
from typing import List, Optional
from jam.core.types import (
    Struct, Field, JAMType, Arr, Vec, Opt,
    encode, decode, EncodeError, DecodeError
)

# Test struct definitions
class Point(Struct):
    """Simple 2D point struct."""
    x: Field[int] = Field(int)
    y: Field[int] = Field(int)

class Rectangle(Struct):
    """Rectangle defined by two points."""
    top_left: Field[Point] = Field(Point)
    bottom_right: Field[Point] = Field(Point)

class ComplexStruct(Struct):
    """Struct using all composite type features."""
    name: Field[str] = Field(str)
    values: Field[List[int]] = Field(List[int])
    flags: Field[List[bool]] = Field(List[bool])
    fixed_data: Field[Arr[int, 3]] = Field(Arr[int, 3])
    coordinates: Field[Vec[Point]] = Field(Vec[Point])
    maybe_value: Field[Optional[int]] = Field(Optional[int])
    matrix: Field[Arr[Arr[int, 2], 2]] = Field(Arr[Arr[int, 2], 2])

class TestStructs:
    """Test suite for struct type system."""

    def test_simple_struct(self):
        """Test basic struct encoding/decoding."""
        point = Point(x=10, y=20)
        encoded = encode(point)
        decoded, size = decode(Point, encoded)
        assert decoded.x == point.x
        assert decoded.y == point.y
        assert size == len(encoded)

    def test_nested_struct(self):
        """Test nested struct encoding/decoding."""
        rect = Rectangle(
            top_left=Point(x=0, y=0),
            bottom_right=Point(x=100, y=100)
        )
        encoded = encode(rect)
        decoded, size = decode(Rectangle, encoded)
        assert decoded.top_left.x == rect.top_left.x
        assert decoded.top_left.y == rect.top_left.y
        assert decoded.bottom_right.x == rect.bottom_right.x
        assert decoded.bottom_right.y == rect.bottom_right.y

    def test_complex_struct(self):
        """Test struct with all composite types."""
        data = ComplexStruct(
            name="test",
            values=[1, 2, 3],
            flags=[True, False],
            fixed_data=[4, 5, 6],
            coordinates=[
                Point(x=0, y=0),
                Point(x=1, y=1)
            ],
            maybe_value=None,
            matrix=[[1, 2], [3, 4]]
        )
        encoded = encode(data)
        decoded, size = decode(ComplexStruct, encoded)
        
        assert decoded.name == data.name
        assert decoded.values == data.values
        assert decoded.flags == data.flags
        assert decoded.fixed_data == data.fixed_data
        assert len(decoded.coordinates) == len(data.coordinates)
        assert decoded.maybe_value == data.maybe_value
        assert decoded.matrix == data.matrix

    def test_type_validation(self):
        """Test type validation in struct fields."""
        with pytest.raises(TypeError):
            Point(x="not an int", y=0)
            
        with pytest.raises(TypeError):
            Point(x=0, y=None)
            
        point = Point(x=0, y=0)
        with pytest.raises(TypeError):
            point.x = "not an int"

    def test_invalid_fixed_array(self):
        """Test validation of fixed-size arrays."""
        class TestStruct(Struct):
            data: Field[Arr[int, 3]] = Field(Arr[int, 3])
            
        with pytest.raises(EncodeError):
            TestStruct(data=[1, 2])  # Too few elements
            
        with pytest.raises(EncodeError):
            TestStruct(data=[1, 2, 3, 4])  # Too many elements

    def test_partial_decode(self):
        """Test handling of partial decoding."""
        point = Point(x=10, y=20)
        encoded = encode(point)
        
        # Try decoding truncated data
        with pytest.raises(DecodeError):
            decode(Point, encoded[:-1])

class TestCompositeTypes:
    """Test suite for composite type combinations."""

    def test_nested_arrays(self):
        """Test nested fixed-size arrays."""
        codec = Arr[Arr[int, 2], 3]
        value = [[1, 2], [3, 4], [5, 6]]
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value

    def test_vector_of_options(self):
        """Test vector of optional values."""
        codec = Vec[Optional[int]]
        value = [1, None, 2, None, 3]
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value

    def test_array_of_vectors(self):
        """Test fixed array of vectors."""
        codec = Arr[Vec[int], 2]
        value = [[1, 2, 3], [4, 5]]
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value

    def test_option_of_array(self):
        """Test optional fixed-size array."""
        codec = Opt[Arr[int, 3]]
        value = [1, 2, 3]
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        
        encoded = codec.encode(None)
        decoded, size = codec.decode_from(encoded)
        assert decoded is None

class TestTypeSystem:
    """Test suite for type system features."""

    def test_type_aliases(self):
        """Test JAM type aliases and constructors."""
        #