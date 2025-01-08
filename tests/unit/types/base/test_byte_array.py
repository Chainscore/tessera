"""Unit tests for byte array type implementations."""

import pytest
from jam.types.base import (
    ByteArray, ByteArray8, ByteArray16, ByteArray32, ByteArray64,
    ByteArray96, ByteArray128, ByteArray144, ByteArray256, ByteArray784
)

def make_test_bytes(size: int) -> bytes:
    """Create test bytes of given size, repeating 0-255 pattern."""
    return bytes(i % 256 for i in range(size))

class TestByteArrayTypes:
    """Test suite for fixed-width byte array type implementations."""

    @pytest.mark.parametrize("array_class,size", [
        (ByteArray8, 8),
        (ByteArray16, 16),
        (ByteArray32, 32),
        (ByteArray64, 64),
        (ByteArray96, 96),
        (ByteArray128, 128),
        (ByteArray144, 144),
        (ByteArray256, 256),
        (ByteArray784, 784),
    ])
    def test_valid_creation(self, array_class, size):
        """Test creation of ByteArray types with valid values."""
        # Test with zeros
        value = bytes(size)
        byte_array = array_class(value)
        assert isinstance(byte_array, array_class)
        assert len(byte_array) == size
        assert bytes(byte_array) == value
        
        # Test with pattern
        value = make_test_bytes(size)
        byte_array = array_class(value)
        assert isinstance(byte_array, array_class)
        assert len(byte_array) == size
        assert bytes(byte_array) == value

    @pytest.mark.parametrize("array_class,size", [
        (ByteArray8, 8),
        (ByteArray16, 16),
        (ByteArray32, 32),
        (ByteArray64, 64),
        (ByteArray96, 96),
        (ByteArray128, 128),
        (ByteArray144, 144),
        (ByteArray256, 256),
        (ByteArray784, 784),
    ])
    def test_invalid_creation(self, array_class, size):
        """Test that creating ByteArray types with invalid lengths raises ValueError."""
        with pytest.raises(ValueError):
            array_class(bytes(size - 1))  # Too short
        with pytest.raises(ValueError):
            array_class(bytes(size + 1))  # Too long

    @pytest.mark.parametrize("array_class,size", [
        (ByteArray8, 8),
        (ByteArray16, 16),
        (ByteArray32, 32),
        (ByteArray64, 64),
        (ByteArray96, 96),
        (ByteArray128, 128),
        (ByteArray144, 144),
        (ByteArray256, 256),
        (ByteArray784, 784),
    ])
    def test_encoding_decoding(self, array_class, size):
        """Test encoding and decoding of ByteArray types."""
        
        value = make_test_bytes(size)
        byte_array = array_class(value)

        # Test encoding
        encoded = byte_array.encode()
        
        # Test decoding
        decoded, decoded_size = array_class.decode_from(encoded)
        assert isinstance(decoded, array_class)
        assert bytes(decoded) == value
        assert decoded_size == size
        
        # Test decoding with offset
        offset = 5
        buffer = bytes(offset) + encoded
        decoded, decoded_size = array_class.decode_from(buffer, offset)
        assert isinstance(decoded, array_class)
        assert bytes(decoded) == value
        assert decoded_size == size

    @pytest.mark.parametrize("array_class,size", [
        (ByteArray8, 8),
        (ByteArray16, 16),
        (ByteArray32, 32),
        (ByteArray64, 64),
        (ByteArray96, 96),
        (ByteArray128, 128),
        (ByteArray144, 144),
        (ByteArray256, 256),
        (ByteArray784, 784),
    ])
    def test_equality(self, array_class, size):
        """Test equality comparison."""
        value1 = make_test_bytes(size)
        value2 = bytes(reversed(make_test_bytes(size)))
        
        arr1 = array_class(value1)
        arr2 = array_class(value1)  # Same value as arr1
        arr3 = array_class(value2)  # Different value
        
        # Test equality with other ByteArray objects
        assert arr1 == arr2
        assert arr1 != arr3
        
        # Test equality with bytes objects
        assert arr1 == value1
        assert arr1 != value2
        
        # Test equality with wrong size
        assert arr1 != bytes(size - 1)
        assert arr1 != bytes(size + 1)
        
        # Test equality with other types
        assert arr1 != 42
        assert arr1 != f"0x{value1.hex()}"

    @pytest.mark.parametrize("array_class,size", [
        (ByteArray8, 8),
        (ByteArray16, 16),
        (ByteArray32, 32),
        (ByteArray64, 64),
        (ByteArray96, 96),
        (ByteArray128, 128),
        (ByteArray144, 144),
        (ByteArray256, 256),
        (ByteArray784, 784),
    ])
    def test_repr(self, array_class, size):
        """Test string representation."""
        value = make_test_bytes(size)
        byte_array = array_class(value)
        expected = f"{array_class.__name__}([{', '.join(f'Byte(0x{byte.to_bytes().hex()})' for byte in value)}])"
        assert repr(byte_array) == expected
