"""
Unit tests for integer codec implementations.

Tests both fixed-width integer codecs and general number encoding according to the
JAM protocol specification.
"""

import pytest
from jam.core.codec.primitives.integers import (
    u8, u16, u32, u64, i8, i16, i32, i64, general,
    get_codec_for_value, IntegerCodec, GeneralCodec,
    EncodeError, DecodeError
)

class TestFixedWidthIntegers:
    """Test fixed-width integer encoding/decoding."""
    
    @pytest.mark.parametrize("codec,value", [
        (u8, 0),
        (u8, 127),
        (u8, 255),
        (u16, 256),
        (u16, 65535),
        (u32, 65536),
        (u32, 4294967295),
        (u64, 4294967296),
        (u64, 18446744073709551615),
        (i8, -128),
        (i8, 0),
        (i8, 127),
        (i16, -32768),
        (i16, 32767),
        (i32, -2147483648),
        (i32, 2147483647),
        (i64, -9223372036854775808),
        (i64, 9223372036854775807),
    ])
    def test_codec_roundtrip(self, codec, value):
        """Test encoding and decoding roundtrip for valid values."""
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)
        assert size == codec.byte_size
        
    @pytest.mark.parametrize("codec,value,expected_error", [
        (u8, -1, EncodeError),
        (u8, 256, EncodeError),
        (u16, -1, EncodeError),
        (u16, 65536, EncodeError),
        (u32, -1, EncodeError),
        (u32, 4294967296, EncodeError),
        (u64, -1, EncodeError),
        (u64, 18446744073709551616, EncodeError),
        (i8, -129, EncodeError),
        (i8, 128, EncodeError),
        (i16, -32769, EncodeError),
        (i16, 32768, EncodeError),
        (i32, -2147483649, EncodeError),
        (i32, 2147483648, EncodeError),
        (i64, -9223372036854775809, EncodeError),
        (i64, 9223372036854775808, EncodeError),
    ])
    def test_codec_value_bounds(self, codec, value, expected_error):
        """Test that out-of-bounds values raise appropriate errors."""
        with pytest.raises(expected_error):
            codec.encode(value)
            
    def test_buffer_size_validation(self):
        """Test encoding into buffers that are too small."""
        for codec in [u8, u16, u32, u64, i8, i16, i32, i64]:
            with pytest.raises(EncodeError):
                codec.encode_into(0, bytearray(codec.byte_size - 1))
                
    def test_decode_insufficient_bytes(self):
        """Test decoding from buffers that are too small."""
        for codec in [u8, u16, u32, u64, i8, i16, i32, i64]:
            with pytest.raises(DecodeError):
                codec.decode_from(bytes(codec.byte_size - 1))


class TestGeneralNumberEncoding:
    """Test general number encoding according to JAM specification."""
    
    @pytest.mark.parametrize("value,expected_size", [
        (0, 1),
        (127, 1),
        (128, 2),
        (16383, 2),
        (16384, 3),
        (2097151, 3),
        (2097152, 4),
        (268435455, 4),
        (268435456, 5),
        (34359738367, 5),
        (34359738368, 6),
        (4398046511103, 6),
        (4398046511104, 7),
        (562949953421311, 7),
        (562949953421312, 8),
        (72057594037927935, 8),
        (72057594037927936, 9),
        (18446744073709551615, 9),  # u64::MAX
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
        # Additional test vectors from specification
        (9223372036854775808, bytes([255, 0, 0, 0, 0, 0, 0, 0, 128])),  # 2^63
        (18446744073709551615, bytes([255, 255, 255, 255, 255, 255, 255, 255, 255])),  # u64::MAX
    ])
    def test_encoding(self, value, expected_encoding):
        """Test encoding specific values produces expected byte sequences."""
        encoded = general.encode(value)
        assert encoded == expected_encoding
        
    @pytest.mark.parametrize("encoded,expected_value", [
        (bytes([0]), 0),
        (bytes([127]), 127),
        (bytes([128, 128]), 128),
        (bytes([128, 255]), 255),
        (bytes([129, 0]), 256),
        (bytes([129, 44]), 300),
        (bytes([131, 232]), 1000),
        # Additional test vectors from specification
        (bytes([255, 0, 0, 0, 0, 0, 0, 0, 128]), 9223372036854775808),  # 2^63
        (bytes([255, 255, 255, 255, 255, 255, 255, 255, 255]), 18446744073709551615),  # u64::MAX
    ])
    def test_decoding(self, encoded, expected_value):
        """Test decoding specific byte sequences produces expected values."""
        decoded, size = general.decode_from(encoded)
        assert decoded == expected_value
        assert size == len(encoded)

    def test_roundtrip_all_sizes(self):
        """Test encoding/decoding roundtrip for different size thresholds."""
        test_values = [
            2**x - 1 for x in range(64)
        ] + [
            2**x for x in range(64)
        ] + [
            2**x + 1 for x in range(64)
        ]
        
        for value in test_values:
            if value > 18446744073709551615:  # u64::MAX
                continue
            encoded = general.encode(value)
            decoded, size = general.decode_from(encoded)
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


class TestCodecSelection:
    """Test codec selection based on value ranges."""
    
    @pytest.mark.parametrize("value,expected_codec", [
        (0, u8),
        (255, u8),
        (256, u16),
        (65535, u16),
        (65536, u32),
        (4294967295, u32),
        (4294967296, u64),
        (18446744073709551615, u64),
        (-1, i8),
        (-128, i8),
        (-129, i16),
        (-32768, i16),
        (-32769, i32),
        (-2147483648, i32),
        (-2147483649, i64),
        (-9223372036854775808, i64),
    ])
    def test_get_codec_for_value(self, value, expected_codec):
        """Test that get_codec_for_value returns appropriate codec for values."""
        codec = get_codec_for_value(value)
        assert codec is expected_codec
        
    def test_value_out_of_range(self):
        """Test that values outside any codec's range raise appropriate error."""
        with pytest.raises(ValueError):
            get_codec_for_value(-9223372036854775809)  # i64::MIN - 1
        with pytest.raises(ValueError):
            get_codec_for_value(18446744073709551616)  # u64::MAX + 1


def test_encoded_bytes_match_spec():
    """Verify encoding matches specific examples from the specification."""
    test_vectors = [
        (u64, 0, bytes([0, 0, 0, 0, 0, 0, 0, 0])),
        (u64, 42, bytes([42, 0, 0, 0, 0, 0, 0, 0])),
        (u32, 16777215, bytes([255, 255, 255, 0])),
        (u16, 65535, bytes([255, 255])),
        (u8, 255, bytes([255])),
    ]
    
    for codec, value, expected in test_vectors:
        encoded = codec.encode(value)
        assert encoded == expected