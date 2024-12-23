"""
Unit tests for integer codec implementations.

Tests both fixed-width integer codecs and general number encoding according to the
JAM protocol specification.
"""

import pytest
from jam.utils.codec.primitives.integers import (
    u8, u16, u32, u64, u128, u256, general,
    U8, U16, U32, U64, U128, U256,
    EncodeError, DecodeError
)

from jam.utils.codec import encode, decode

class TestFixedWidthIntegers:
    """Test fixed-width integer encoding/decoding."""
    
    @pytest.mark.parametrize("size,value", [
        (8, U8(0)),
        (8, U8(127)),
        (8, U8(128)),
        (8, U8(255)),
        (16, U16(256)),
        (16, U16(2**16-1)),
        (32, U32(2**32-1)),
        (64, U64(2**32)),
        (64, U64(2**64-1)),
        (128, U128(2**64)),
        (128, U128(2**128-1)),
        (256, U256(2**128)),
        (256, U256(2**256-1)),
    ])
    def test_codec_roundtrip(self, size, value):
        """Test encoding and decoding roundtrip for valid values."""
        encoded = encode(value)
        decoded, size = decode(type(value), encoded)
        assert decoded == value
        assert size == len(encoded)
        
    @pytest.mark.parametrize("value,expected_error", [
        (U8(-1), EncodeError),
        (U8(256), EncodeError),
        (U16(-1), EncodeError),
        (U16(2**16), EncodeError),
        (U32(-1), EncodeError),
        (U32(2**32), EncodeError),
        (U64(-1), EncodeError),
        (U64(2**64), EncodeError),
        (U128(-1), EncodeError),
        (U128(2**128), EncodeError),
        (U256(-1), EncodeError),
        (U256(2**256), EncodeError),
    ])
    def test_codec_value_bounds(self, value, expected_error):
        """Test that out-of-bounds values raise appropriate errors."""
        with pytest.raises(expected_error):
            encode(value)
            
    def test_buffer_size_validation(self):
        """Test encoding into buffers that are too small."""
        for codec in [u8, u16, u32, u64, u128, u256]:
            with pytest.raises(EncodeError):
                codec.encode_into(0, bytearray(codec.byte_size - 1))
                
    def test_decode_insufficient_bytes(self):
        """Test decoding from buffers that are too small."""
        for codec in [u8, u16, u32, u64, u128, u256]:
            with pytest.raises(DecodeError):
                codec.decode_from(bytes(codec.byte_size - 1))


class TestGeneralNumberEncoding:
    """Test general number encoding according to JAM specification."""
    
    @pytest.mark.parametrize("value,expected_size", [
        (0, 1),
        (2**7-1, 1),
        (2**7, 2),
        (2**14-1, 2),
        (2**14, 3),
        (2**21-1, 3),
        (2**21, 4),
        (2**28-1, 4),
        (2**28, 5),
        (2**35-1, 5),
        (2**35, 6),
        (2**42-1, 6),
        (2**42, 7),
        (2**49-1, 7),
        (2**49, 8),
        (2**56-1, 8),
        (2**56, 9),
        (2**63-1, 9),
        (2**63+1, 9),
        (2**64-1, 9),
    ])
    def test_encode_size(self, value, expected_size):
        """Test that encode_size returns correct sizes for different values."""
        assert general.encode_size(value) == expected_size

    @pytest.mark.parametrize("value,expected_encoding", [
        (0, bytes([0])),
        (127, bytes([127])),
        (128, bytes([128, 128])),
        (255, bytes([128, 255])),
        (256, bytes([129, 0])),
        (300, bytes([129, 44])),
        (1000, bytes([131, 232])),
        (9223372036854775808, bytes([255, 0, 0, 0, 0, 0, 0, 0, 128])),  # 2^63
        (18446744073709551615, bytes([255, 255, 255, 255, 255, 255, 255, 255, 255])),  # u64::MAX
    ])
    def test_encoding(self, value, expected_encoding):
        """Test encoding specific values produces expected byte sequences."""
        encoded = encode(value)
        assert encoded == expected_encoding
        
    @pytest.mark.parametrize("encoded,expected_value", [
        (bytes([0]), 0),
        (bytes([127]), 127),
        (bytes([128, 128]), 128),
        (bytes([128, 255]), 255),
        (bytes([129, 0]), 256),
        (bytes([129, 44]), 300),
        (bytes([131, 232]), 1000),
        (bytes([255, 0, 0, 0, 0, 0, 0, 0, 128]), 2**63),  # 2^63
        (bytes([255, 255, 255, 255, 255, 255, 255, 255, 255]), 2**64 - 1),  # u64::MAX
    ])
    def test_decoding(self, encoded, expected_value):
        """Test decoding specific byte sequences produces expected values."""
        decoded, size = decode(int, encoded)
        assert decoded == expected_value
        assert size == len(encoded)

    def test_roundtrip_all_sizes(self):
        """Test encoding/decoding roundtrip for different size thresholds."""
        test_values = [
            2**x - 1 for x in range(64)
        ] + [
            2**x for x in range(63)
        ] + [
            2**x + 1 for x in range(63)
        ]

        for value in test_values:
            if value > 18446744073709551615:  # u64::MAX
                continue

            print("value -----", value)
            encoded = encode(value)
            decoded, size = decode(int, encoded)
            assert decoded == value
            assert size == len(encoded)
            
    def test_negative_values(self):
        """Test that negative values raise appropriate errors."""
        with pytest.raises(EncodeError):
            general.encode(-1)
            
    def test_too_large_values(self):
        """Test that values larger than u64::MAX raise appropriate errors."""
        with pytest.raises(EncodeError):
            general.encode(18446744073709551616)  # u64::MAX + 1