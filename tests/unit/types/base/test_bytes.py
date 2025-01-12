"""Unit tests for bytes type implementation."""

import pytest
from jam.types.base.bytes import Bytes

class TestBytesType:
    """Test suite for bytes type implementation."""

    def test_bytes_initialization(self):
        """Test initialization with different input types."""
        # Test with bytes
        b1 = Bytes(b'hello')
        assert len(b1) == 5
        assert bytes(b1) == b'hello'

        # Test with hex string (no prefix)
        b2 = Bytes('48656c6c6f')  # 'hello' in hex
        assert len(b2) == 5
        assert bytes(b2) == b'Hello'

        # Test with hex string (0x prefix)
        b3 = Bytes('0x48656c6c6f')  # 'hello' in hex
        assert len(b3) == 5
        assert bytes(b3) == b'Hello'

        # Test with single byte integer
        b4 = Bytes(65)  # ASCII 'A'
        assert len(b4) == 1
        assert bytes(b4) == b'A'

    def test_bytes_equality(self):
        """Test equality comparison."""
        b1 = Bytes(b'hello')
        b2 = Bytes(b'hello')
        b3 = Bytes(b'world')

        # Test equality with other Bytes objects
        assert b1 == b2
        assert b1 != b3

        # Test equality with bytes objects
        assert b1 == b'hello'
        assert b1 != b'world'

        # Test equality with other types
        assert b1 != 42
        assert b1 != "hello"

    def test_bytes_codec_roundtrip(self):
        """Test encoding and decoding roundtrip."""
        original = Bytes(b'hello world')
        
        # Test encoding
        encoded = original.encode()
        
        # Test decoding
        decoded, size = Bytes.decode_from(encoded)
        
        # Verify roundtrip
        assert decoded == original
        assert size == len(encoded)

    def test_bytes_repr(self):
        """Test string representation."""
        b = Bytes(b'hello')
        expected = "Bytes(0x68656c6c6f)"  # 'hello' in hex
        assert repr(b) == expected

    def test_invalid_hex_string(self):
        """Test initialization with invalid hex string."""
        with pytest.raises(ValueError):
            Bytes('invalid hex') 