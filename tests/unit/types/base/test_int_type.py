"""Unit tests for fixed-width integer types."""

import pytest
from jam.types.base.integers import U8, U16, U32, U64, U128, U256, U512


class TestFixedIntTypes:
    """Test fixed-width integer type implementations."""

    @pytest.mark.parametrize(
        "int_class,value,byte_size",
        [
            (U8, U8(255), 1),
            (U16, U16(65535), 2),
            (U32, U32(4294967295), 4),
            (U64, U64(18446744073709551615), 8),
            (U128, U128(2**128 - 1), 16),
            (U256, U256(2**256 - 1), 32),
            (U512, U512(2**512 - 1), 64),
        ],
    )
    def test_valid_creation(self, int_class, value, byte_size):
        """Test creation of fixed-width integers with valid values."""
        num = int_class(value)
        assert isinstance(num, int_class)
        assert int(num) == value
        assert num.byte_size == byte_size

    @pytest.mark.parametrize(
        "int_class,invalid_value",
        [
            (U8, -1),
            (U8, 256),
            (U16, -1),
            (U16, 2**16),
            (U32, -1),
            (U32, 2**32),
            (U64, -1),
            (U64, 2**64),
        ],
    )
    def test_invalid_creation(self, int_class, invalid_value):
        """Test that creating fixed-width integers with invalid values raises ValueError."""
        with pytest.raises(ValueError):
            int_class(invalid_value)

    def test_encoding_decoding(self):
        """Test encoding and decoding of fixed-width integers."""
        test_cases = [
            (U8(123), 1),
            (U16(1000), 2),
            (U32(100000), 4),
            (U64(1000000), 8),
        ]

        for value, expected_size in test_cases:
            # Test encode_size
            assert value.encode_size() == expected_size

            # Test encode_into and decode_from
            buffer = bytearray(expected_size)
            encoded_size = value.encode_into(buffer)
            assert encoded_size == expected_size

            decoded_value, decoded_size = value.decode_from(bytes(buffer))
            assert decoded_value == int(value)
            assert decoded_size == expected_size

    def test_decimal_compatibility(self):
        """Test that fixed-width integers work with Decimal operations."""
        a = U8(100)
        b = U8(50)

        # Test basic arithmetic
        assert int(a + b) == 150
        assert int(a - b) == 50
        assert int(U16(a) * U16(b)) == 5000  # Note: This might overflow in real usage
        assert float(a / b) == 2.0
