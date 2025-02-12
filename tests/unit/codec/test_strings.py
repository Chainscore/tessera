"""
Unit tests for string codec implementation.
"""

import pytest
from jam.utils.codec.primitives.strings import (
    StringCodec,
    EncodeError,
    DecodeError,
    string_codec,
)


class TestStringCodec:
    """Test suite for string encoding/decoding."""

    @pytest.mark.parametrize(
        "test_str",
        [
            "",  # Empty string
            "Hello, world!",  # ASCII
            "Hello, 世界！",  # Mixed ASCII and Unicode
            "🦀 Rust 🚀",  # Emojis
            "α β γ δ ε",  # Greek letters
            "Привет, мир!",  # Cyrillic
            "안녕하세요",  # Korean
            "你好，世界！",  # Chinese
            "🏳️‍🌈",  # Complex emoji with modifiers
            "\u0000\u0001\u0002",  # Control characters
            "a" * 1000,  # Longer string
            "❤️" * 100,  # Repeated emojis
        ],
    )
    def test_roundtrip(self, test_str):
        """Test encoding and decoding roundtrip for various strings."""
        encoded = string_codec.encode(test_str)
        decoded, size = string_codec.decode_from(encoded)
        assert decoded == test_str
        assert size == len(encoded)
        assert size == StringCodec().encode_size(test_str)

    def test_length_prefix(self):
        """Test that length prefix is correctly encoded."""
        test_str = "Hello"
        encoded = string_codec.encode(test_str)

        # First byte should be length (5)
        expected_prefix = bytes([5])
        assert encoded[:1] == expected_prefix

        # Following bytes should be UTF-8 encoded string
        assert encoded[1:] == test_str.encode("utf-8")

    def test_empty_string(self):
        """Test handling of empty strings."""
        encoded = string_codec.encode("")
        # Should just be 8 zero bytes for length
        assert encoded == bytes([0] * 1)

        decoded, size = string_codec.decode_from(encoded)
        assert decoded == ""
        assert size == 1

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        test_str = "Test string"
        size = string_codec.encode_size(test_str)

        # Test encoding into too small buffer
        with pytest.raises(EncodeError):
            string_codec.encode_into(test_str, bytearray(size - 1))

        # Test decoding from too small buffer
        encoded = string_codec.encode(test_str)
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                string_codec.decode_from(encoded[:i])

    def test_invalid_types(self):
        """Test that non-string values raise appropriate errors."""
        invalid_values = [
            42,  # int
            3.14,  # float
            True,  # bool
            None,  # NoneType
            b"bytes",  # bytes
            bytearray(),  # bytearray
            ["list"],  # list
            {"dict"},  # dict
        ]

        for value in invalid_values:
            with pytest.raises(EncodeError):
                string_codec.encode(value)

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        test_str = "Test"
        buffer_size = string_codec.encode_size(test_str)

        # Create buffer with padding
        buffer = bytearray([0xFF] * (buffer_size + 2))

        # Test encoding at offset
        written = string_codec.encode_into(test_str, buffer, 1)
        assert written == buffer_size

        # Test decoding at offset
        decoded, size = string_codec.decode_from(buffer, 1)
        assert decoded == test_str
        assert size == buffer_size

        # Verify padding wasn't overwritten
        assert buffer[0] == 0xFF
        assert buffer[-1] == 0xFF

    def test_large_string(self):
        """Test handling of large strings."""
        # Test string just under limit
        large_str = "x" * (2**20)  # 1MB string
        decoded, size = string_codec.decode_from(string_codec.encode(large_str))
        assert decoded == large_str
        assert size == len(string_codec.encode(large_str))

    def test_invalid_utf8_sequence(self):
        """Test handling of invalid UTF-8 sequences."""
        # Create invalid UTF-8 sequence
        invalid_buffer = bytearray([5, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])  # Invalid UTF-8

        with pytest.raises(DecodeError):
            string_codec.decode_from(invalid_buffer)

    @pytest.mark.parametrize(
        "string,expected_size",
        [
            ("", 1),  # Empty string: just length prefix
            ("a", 2),  # Single ASCII: length + 1 byte
            ("α", 3),  # Single Greek: length + 2 bytes
            ("🦀", 5),  # Single emoji: length + 4 bytes
            ("Hello", 6),  # ASCII string: length + 5 bytes
            ("Hello, 世界", 14),  # Mixed string: length + variable bytes
        ],
    )
    def test_specific_sizes(self, string, expected_size):
        """Test that specific strings encode to expected sizes."""
        encoded = string_codec.encode(string)
        assert len(encoded) == expected_size
        assert string_codec.encode_size(string) == expected_size

    def test_manual_decode_matches_codec(self):
        """Verify that our understanding of the format matches implementation."""
        import struct

        test_str = "Hello, world!"
        encoded = string_codec.encode(test_str)

        # Manual decode
        content = bytes(encoded[1:]).decode("utf-8")

        # Should match codec decode
        decoded, size = string_codec.decode_from(encoded)
        assert content == decoded
        assert size == len(encoded)
