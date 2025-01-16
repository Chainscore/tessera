"""Unit tests for byte array type implementations."""

import pytest
from jam.types.base import (
    ByteArray8, ByteArray16, ByteArray32, ByteArray64,
    ByteArray96, ByteArray128, ByteArray144, ByteArray256, ByteArray784
)
from jam.types.base.byte import Byte
from jam.types.base.bytes import Bytes

def make_test_bytes(size: int) -> Bytes:
    """Create test bytes of given size, repeating 0-255 pattern."""
    return Bytes([Byte(i % 256) for i in range(size)])

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
        value = Bytes([0] * size)
        byte_array = array_class(value)
        assert isinstance(byte_array, array_class)
        assert len(byte_array) == size
        assert bytes(byte_array) == bytes(value)
        
        # Test with pattern
        value = make_test_bytes(size)
        byte_array = array_class(value)
        assert isinstance(byte_array, array_class)
        assert len(byte_array) == size
        assert bytes(byte_array) == bytes(value)

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
        assert bytes(decoded) == bytes(value)
        assert decoded_size == size
        
        # Test decoding with offset
        offset = 5
        buffer = bytes(offset) + encoded
        decoded, decoded_size = array_class.decode_from(buffer, offset)
        assert isinstance(decoded, array_class)
        assert bytes(decoded) == bytes(value)
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
        value2 = Bytes(reversed(value1.value))
        
        arr1 = array_class(value1)
        arr2 = array_class(value1)  # Same value as arr1
        arr3 = array_class(value2)  # Different value
        
        # Test equality with other ByteArray objects
        assert arr1 == arr2
        assert arr1 != arr3
        
        # Test equality with bytes objects
        assert arr1.value == value1.value
        assert arr1 != value2
        
        # Test equality with wrong size
        assert arr1.value != bytes(size - 1)
        assert arr1.value != bytes(size + 1)
        
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
        expected = f"{array_class.__name__}([{', '.join(f'{(byte)}' for byte in value)}])"
        assert repr(byte_array) == expected
        
    @pytest.mark.parametrize("array_class,in_range,out_of_range", [
        (ByteArray8, 8, 9),
        (ByteArray16, 16, 17),
        (ByteArray32, 32, 33),
        (ByteArray64, 64, 65),
        (ByteArray96, 96, 97),
        (ByteArray128, 128, 129),
        (ByteArray144, 144, 145),
        (ByteArray256, 256, 257),
        (ByteArray784, 784, 785),
    ])
    def test_fail_on_more_than_length(self, array_class, in_range, out_of_range):
        """Test that creating ByteArray types with invalid lengths raises ValueError."""
        with pytest.raises(ValueError):
            array_class(bytearray(out_of_range))  # Too long