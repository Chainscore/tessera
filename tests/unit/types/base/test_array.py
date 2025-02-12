"""Unit tests for array type implementation."""

import pytest
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.integers.fixed import U8

@decodable_array(length=4, element_type=U8)  # Fixed length array of U8s for testing
class TestArray(Array[U8]): ...

class TestArrayTypes:
    """Test suite for array type implementations."""

    def test_array_initialization(self):
        """Test array initialization."""
        # Test initialization with values
        arr = TestArray([U8(1), U8(2), U8(3), U8(4)])
        assert len(arr) == 4
        assert list(arr) == [U8(1), U8(2), U8(3), U8(4)]

        # Test initialization with wrong length
        with pytest.raises(ValueError):
            TestArray([U8(1), U8(2), U8(3)])  # Too few
        with pytest.raises(ValueError):
            TestArray([U8(1), U8(2), U8(3), U8(4), U8(5)])  # Too many

        # Test initialization with wrong type
        with pytest.raises(TypeError):
            TestArray([1, 2, 3, 4])  # Raw ints instead of U8s # type: ignore

    def test_array_codec_roundtrip(self):
        """Test encoding and decoding roundtrip."""
        arr = TestArray([U8(1), U8(2), U8(3), U8(4)])
        
        # Test encoding
        encoded = arr.encode()
        
        # Test decoding
        decoded, size = TestArray.decode_from(encoded)
        assert decoded == arr
        assert size == len(encoded)

    def test_array_sequence_protocol(self):
        """Test sequence protocol implementation."""
        arr = TestArray([U8(1), U8(2), U8(3), U8(4)])
        
        # Test length
        assert len(arr) == 4
        
        # Test iteration
        assert all(isinstance(item, U8) for item in arr)
        
        # Test indexing
        assert arr[0] == U8(1)
        assert arr[-1] == U8(4)
        
        # Test slicing
        assert arr[1:3] == [U8(2), U8(3)]
        
        # Test index out of bounds
        with pytest.raises(IndexError):
            _ = arr[10]

    def test_array_mutation(self):
        """Test array mutation operations."""
        arr = TestArray([U8(1), U8(2), U8(3), U8(4)])
        
        # Test item assignment
        arr[0] = U8(5)
        assert arr[0] == U8(5)
        
        # Test invalid assignment
        with pytest.raises(TypeError):
            arr[0] = 5  # Raw int instead of U8 # type: ignore
            
        with pytest.raises(IndexError):
            arr[10] = U8(1)

    def test_array_equality(self):
        """Test array equality comparison."""
        arr1 = TestArray([U8(1), U8(2), U8(3), U8(4)])
        arr2 = TestArray([U8(1), U8(2), U8(3), U8(4)])
        arr3 = TestArray([U8(5), U8(6), U8(7), U8(8)])
        
        assert arr1 == arr2
        assert arr1 != arr3
        assert arr1 == [U8(1), U8(2), U8(3), U8(4)]  # Compare with list of U8s
        assert arr1 == [1, 2, 3, 4]  # Compare with raw ints

    def test_array_repr(self):
        """Test array string representation."""
        arr = TestArray([U8(1), U8(2), U8(3), U8(4)])
        expected = "TestArray([U8(1), U8(2), U8(3), U8(4)])"
        assert repr(arr) == expected
