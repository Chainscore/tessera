"""Unit tests for Option type implementation."""

import pytest
from typing import TypeVar, cast

from jam.types.base.option import Option
from jam.types.base.boolean import Boolean
from jam.types.base.integers import Int
from jam.utils.codec.base import DecodeError, Codable

T = TypeVar('T', bound=Codable)

class TestOption:
    """Test suite for Option type."""

    def test_basic_option(self):
        """Test basic Option functionality."""
        # Test with None
        opt_none = Option(type=Int, value=None)
        assert opt_none.get() is None
        assert str(opt_none) == "Option(None)"
        assert repr(opt_none) == "Option(None)"

        # Test with value
        opt_value = Option(type=Int, value=Int(42))
        assert opt_value.get() == Int(42)
        assert str(opt_value) == "Option(Int(42))"
        assert repr(opt_value) == "Option(Int(42))"

    def test_type_validation(self):
        """Test type validation during initialization."""
        # Valid cases
        Option(type=Int)  # None is always valid
        Option(type=Int, value=Int(42))  # Correct type
        Option(type=Boolean, value=Boolean(True))  # Another valid type

        # Invalid cases
        with pytest.raises(TypeError):
            Option(type=Int, value=cast(Int, 42))  # Raw int not allowed
        with pytest.raises(TypeError):
            Option(type=Int, value=cast(Int, Boolean(True)))  # Wrong type
        with pytest.raises(TypeError):
            Option(type=Int, value=cast(Int, "not an int"))  # Wrong type

    def test_encode_decode(self):
        """Test encoding/decoding of Option values."""
        # Test with None
        opt_none = Option(type=Int)
        encoded_none = opt_none.encode()
        decoded_none, size_none = Option.decode_from(buffer=encoded_none, type=Int)
        assert isinstance(decoded_none, Option)
        assert decoded_none.get() is None
        assert size_none == 1  # Tag byte

        # Test with value
        opt_value = Option(type=Int, value=Int(42))
        encoded_value = opt_value.encode()
        decoded_value, size_value = Option.decode_from(buffer=encoded_value, type=Int)
        assert isinstance(decoded_value, Option)
        assert decoded_value.get() == Int(42)
        assert size_value > 1  # Tag byte + encoded value

    def test_equality(self):
        """Test equality comparison."""
        opt1 = Option(type=Int)
        opt2 = Option(type=Int)
        opt3 = Option(type=Int, value=Int(42))
        opt4 = Option(type=Int, value=Int(42))
        opt5 = Option(type=Int, value=Int(43))
        opt6 = Option(type=Boolean)

        # Same type, same value
        assert opt1 == opt2
        assert opt3 == opt4

        # Same type, different value
        assert opt1 != opt3
        assert opt3 != opt5

        # Different type
        assert opt1 != opt6

        # Compare with None
        assert opt1 == None  # noqa: E711
        assert opt3 != None  # noqa: E711

        # Compare with raw values
        assert opt3 == 42
        assert opt3 == Int(42)  # Option[Int](42) != Int(42)

    def test_buffer_operations(self):
        """Test buffer operations."""
        # Test with None
        opt_none = Option(type=Int)
        assert opt_none.encode_size() == 1  # Just tag byte
        
        buffer = bytearray([0xFF] * 10)
        written = opt_none.encode_into(buffer, 5)
        assert written == 1
        assert buffer[5] == 0  # Tag byte for None

        # Test with value
        opt_value = Option(type=Int, value=Int(42))
        size = opt_value.encode_size()
        assert size > 1  # Tag byte + encoded value
        
        buffer = bytearray([0xFF] * 10)
        written = opt_value.encode_into(buffer, 5)
        assert written == size
        assert buffer[5] == 1  # Tag byte for Some

    def test_decode_offset(self):
        """Test decoding with offset."""
        # Prepare a buffer with both None and Some values
        buffer = bytearray([0xFF] * 10)
        opt_none = Option(type=Int)
        opt_value = Option(type=Int, value=Int(42))
        
        # Write None at offset 2
        opt_none.encode_into(buffer, 2)
        decoded_none, size_none = Option.decode_from(buffer=buffer, type=Int, offset=2)
        assert isinstance(decoded_none, Option)
        assert decoded_none.get() is None
        
        # Write Some at offset 5
        opt_value.encode_into(buffer, 5)
        decoded_value, size_value = Option.decode_from(buffer=buffer, type=Int, offset=5)
        assert isinstance(decoded_value, Option)
        assert decoded_value.get() == Int(42)

    def test_invalid_decode(self):
        """Test decoding invalid data."""
        # Invalid tag byte
        buffer = bytearray([0xFF])  # Invalid tag
        with pytest.raises(DecodeError):
            Option.decode_from(buffer=buffer, type=Int)

        # Truncated buffer for Some value
        buffer = bytearray([1])  # Tag for Some but no value
        with pytest.raises(DecodeError):
            Option.decode_from(buffer=buffer, type=Int) 