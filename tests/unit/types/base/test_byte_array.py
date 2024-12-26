import pytest
from jam.types.base.byte_array import (
    ByteArray, ByteArray8, ByteArray16, ByteArray32, ByteArray64,
    ByteArray96, ByteArray128, ByteArray144, ByteArray256, ByteArray784
)

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
        value = bytes(size)
        byte_array = array_class(value)
        assert isinstance(byte_array, array_class)
        # assert len(byte_array) == size
        # assert byte_array.size == size

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
            array_class(bytes(size - 1))
        with pytest.raises(ValueError):
            array_class(bytes(size + 1))

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
        value = bytes(size)
        byte_array = array_class(value)

        # Test encode_size
        assert byte_array.encode_size() == size

        # Test encode_into and decode_from
        buffer = bytearray(size)
        encoded_size = byte_array.encode_into(buffer)
        assert encoded_size == size

        decoded_value, decoded_size = byte_array.decode_from(bytes(buffer))
        assert decoded_value == value
        assert decoded_size == size