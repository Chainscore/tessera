"""Unit tests for null codec implementation."""

import pytest
from typing import Any, Optional, Type, TypeVar, cast

from jam.types.base.null import Null
from jam.utils.codec.base import EncodeError, DecodeError, Codable
from jam.utils.codec.primitives.nulls import NullCodec

class TestNullCodec:
    """Test suite for null encoding/decoding."""

    def test_basic_null(self):
        """Test basic encoding/decoding of null values."""
        codec = NullCodec()
        encoded = codec.encode(None)
        assert encoded == b""
        decoded, size = codec.decode_from(buffer=encoded)
        assert decoded is None
        assert size == 0

    def test_encode_size(self):
        """Test that encode_size always returns 0."""
        codec = NullCodec()
        assert codec.encode_size(None) == 0

    def test_encode_into(self):
        """Test encoding into buffer."""
        codec = NullCodec()
        buffer = bytearray([0xFF] * 10)
        written = codec.encode_into(None, buffer, 5)
        assert written == 0
        assert buffer == bytearray([0xFF] * 10)  # Buffer unchanged

    def test_invalid_value(self):
        """Test handling of non-None values."""
        codec = NullCodec()
        invalid_values = [
            42,              # int
            "not null",      # str
            [],             # list
            {},             # dict
            True,           # bool
            b"",            # bytes
            Null(),         # Null instance
        ]
        
        for value in invalid_values:
            with pytest.raises(EncodeError) as exc_info:
                codec.encode(value)
            assert "Value must be None" in str(exc_info.value)

    def test_global_instance(self):
        """Test that global codec instance works correctly."""
        encoded = NullCodec().encode(None)
        assert encoded == b""
        decoded, size = NullCodec().decode_from(buffer=encoded)
        assert decoded is None
        assert size == 0

    def test_decode_offset(self):
        """Test decoding with offset."""
        codec = NullCodec()
        buffer = bytearray([0xFF] * 10)
        decoded, size = codec.decode_from(buffer=buffer, offset=5)
        assert decoded is None
        assert size == 0
        assert buffer == bytearray([0xFF] * 10)  # Buffer unchanged

    def test_singleton(self):
        """Test that NullCodec instances are singletons."""
        codec1 = NullCodec
        codec2 = NullCodec
        assert codec1 is codec2  # Same instance
        assert codec1 is NullCodec  # Same as global instance

class TestNull:
    """Test suite for Null type."""

    def test_basic_null(self):
        """Test basic Null functionality."""
        null = Null()
        assert null.get() is None
        assert str(null) == "Null()"
        assert repr(null) == "Null()"

    def test_encode_decode(self):
        """Test encoding/decoding of Null values."""
        null = Null()
        encoded = null.encode()
        assert encoded == b""
        decoded, size = Null.decode_from(encoded)
        assert isinstance(decoded, Null)
        assert decoded == null
        assert size == 0

    def test_equality(self):
        """Test equality comparison."""
        null1 = Null()
        null2 = Null()
        assert null1 == null2
        assert null1 == None  # noqa: E711
        assert null1 != "not null"
        assert null1 != 42
        assert null1 != True

    def test_buffer_operations(self):
        """Test buffer operations."""
        null = Null()
        
        # Test encode_size
        assert null.encode_size() == 0
        
        # Test encode_into
        buffer = bytearray([0xFF] * 10)
        written = null.encode_into(buffer, 5)
        assert written == 0
        assert buffer == bytearray([0xFF] * 10)  # Buffer unchanged

    def test_decode_offset(self):
        """Test decoding with offset."""
        buffer = bytearray([0xFF] * 10)
        decoded, size = Null.decode_from(buffer, 5)
        assert isinstance(decoded, Null)
        assert size == 0
        assert buffer == bytearray([0xFF] * 10)  # Buffer unchanged 