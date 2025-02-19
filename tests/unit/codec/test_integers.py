"""
Unit tests for integer codec implementations.

Tests both fixed-width integer codecs and general number encoding according to the
JAM protocol specification.
"""

import pytest
from jam.utils.codec.errors import EncodeError, DecodeError

from jam.types.base.integers import U8, U16, U32, U64, U128, U256, Int


class TestFixedWidthIntegers:
    """Test fixed-width integer encoding/decoding."""

    @pytest.mark.parametrize(
        "value",
        [
            (U8(0)),
            (U8(127)),
            (U8(128)),
            (U8(255)),
            (U16(256)),
            (U16(2**16 - 1)),
            (U32(2**32 - 1)),
            (U64(2**32)),
            (U64(2**64 - 1)),
            (U128(2**64)),
            (U128(2**128 - 1)),
            (U256(2**128)),
            (U256(2**256 - 1)),
        ],
    )
    def test_codec_roundtrip(self, value):
        """Test encoding and decoding roundtrip for valid values."""
        encoded = value.encode()
        decoded, size = value.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    @pytest.mark.parametrize(
        "_type,value,expected_error",
        [
            (U8, -1, ValueError),
            (U8, 256, ValueError),
            (U16, -1, ValueError),
            (U16, 2**16, ValueError),
            (U32, -1, ValueError),
            (U32, 2**32, ValueError),
            (U64, -1, ValueError),
            (U64, 2**64, ValueError),
            (U128, -1, ValueError),
            (U128, 2**128, ValueError),
            (U256, -1, ValueError),
            (U256, 2**256, ValueError),
        ],
    )
    def test_codec_value_bounds(self, _type, value, expected_error):
        """Test that out-of-bounds values raise appropriate errors."""
        with pytest.raises(expected_error):
            _type(value).encode()

    def test_buffer_size_validation(self):
        """Test encoding into buffers that are too small."""
        for value in [U8(0), U16(0), U32(0), U64(0), U128(0), U256(0)]:
            with pytest.raises(EncodeError):
                len(bytearray(value.byte_size - 1))
                value.encode_into(bytearray(value.byte_size - 1))

    def test_decode_insufficient_bytes(self):
        """Test decoding from buffers that are too small."""
        for value in [U8(0), U16(0), U32(0), U64(0), U128(0), U256(0)]:
            with pytest.raises(DecodeError):
                value.decode_from(bytes(value.byte_size - 1))


class TestGeneralNumberEncoding:
    """Test general number encoding according to JAM specification."""

    @pytest.mark.parametrize(
        "value,expected_size",
        [
            (Int(0), 1),
            (Int(2**7 - 1), 1),
            (Int(2**7), 2),
            (Int(2**14 - 1), 2),
            (Int(2**14), 3),
            (Int(2**21 - 1), 3),
            (Int(2**21), 4),
            (Int(2**28 - 1), 4),
            (Int(2**28), 5),
            (Int(2**35 - 1), 5),
            (Int(2**35), 6),
            (Int(2**42 - 1), 6),
            (Int(2**42), 7),
            (Int(2**49 - 1), 7),
            (Int(2**49), 8),
            (Int(2**56 - 1), 8),
            (Int(2**56), 9),
            (Int(2**63 - 1), 9),
            (Int(2**63 + 1), 9),
            (Int(2**64 - 1), 9),
        ],
    )
    def test_encode_size(self, value, expected_size):
        """Test that encode_size returns correct sizes for different values."""
        assert value.encode_size() == expected_size

    @pytest.mark.parametrize(
        "value,expected_encoding",
        [
            (Int(0), bytes([0])),
            (Int(127), bytes([127])),
            (Int(128), bytes([128, 128])),
            (Int(255), bytes([128, 255])),
            (Int(256), bytes([129, 0])),
            (Int(300), bytes([129, 44])),
            (Int(1000), bytes([131, 232])),
            (Int(9223372036854775808), bytes([255, 0, 0, 0, 0, 0, 0, 0, 128])),  # 2^63
            (
                Int(18446744073709551615),
                bytes([255, 255, 255, 255, 255, 255, 255, 255, 255]),
            ),  # u64::MAX
        ],
    )
    def test_encoding(self, value, expected_encoding):
        """Test encoding specific values produces expected byte sequences."""
        encoded = value.encode()
        assert encoded == expected_encoding

    @pytest.mark.parametrize(
        "encoded,expected_value",
        [
            (bytes([0]), 0),
            (bytes([127]), 127),
            (bytes([128, 128]), 128),
            (bytes([128, 255]), 255),
            (bytes([129, 0]), 256),
            (bytes([129, 44]), 300),
            (bytes([131, 232]), 1000),
            (bytes([255, 0, 0, 0, 0, 0, 0, 0, 128]), 2**63),  # 2^63
            (
                bytes([255, 255, 255, 255, 255, 255, 255, 255, 255]),
                2**64 - 1,
            ),  # u64::MAX
        ],
    )
    def test_decoding(self, encoded, expected_value):
        """Test decoding specific byte sequences produces expected values."""
        decoded, size = Int.decode_from(encoded)
        assert decoded == expected_value
        assert size == len(encoded)

    def test_roundtrip_all_sizes(self):
        """Test encoding/decoding roundtrip for different size thresholds."""
        test_values = (
            [2**x - 1 for x in range(64)]
            + [2**x for x in range(63)]
            + [2**x + 1 for x in range(63)]
        )

        for value in test_values:
            print(f"Encoding value: {value}")
            encoded = Int(value).encode()
            decoded, size = Int.decode_from(encoded)
            assert decoded == value
            assert size == len(encoded)

    def test_negative_values(self):
        """Test that negative values raise appropriate errors."""
        with pytest.raises(ValueError):
            Int(-1).encode()

    def test_too_large_values(self):
        """Test that values larger than u64::MAX raise appropriate errors."""
        with pytest.raises(ValueError):
            Int(18446744073709551616).encode()  # u64::MAX + 1
