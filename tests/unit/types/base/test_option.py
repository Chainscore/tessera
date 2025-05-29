"""Unit tests for Option type implementation."""

import pytest
from typing import TypeVar, cast

from jam.types.base.composite import Option
from jam.types.base.boolean import Boolean
from jam.types.base.composite.option import decodable_option
from jam.types.base.integers import Int
from jam.utils.codec.codable import Codable
from jam.utils.codec.errors import DecodeError

T = TypeVar("T", bound=Codable)


@decodable_option(Int)
class OptionalInt(Option):
    ...


@decodable_option(Boolean)
class OptionalBoolean(Option):
    ...


class TestOption:
    """Test suite for Option type."""

    def test_basic_option(self):
        """Test basic Option functionality."""
        # Test with None

        opt_none = OptionalInt()
        assert opt_none == None
        assert str(opt_none) == "OptionalInt(Null)"
        assert repr(opt_none) == "OptionalInt(Null)"

        # Test with value
        opt_value = OptionalInt(Int(42))
        assert opt_value == Int(42)
        assert str(opt_value) == "OptionalInt(Int(42))"
        assert repr(opt_value) == "OptionalInt(Int(42))"

    def test_type_validation(self):
        """Test type validation during initialization."""
        # Valid cases
        OptionalInt()  # None is always valid
        OptionalInt(Int(42))  # Correct type
        OptionalBoolean(Boolean(True))  # Another valid type

        # Invalid cases
        with pytest.raises(ValueError):
            OptionalInt(42)  # Raw int not allowed
        with pytest.raises(ValueError):
            OptionalBoolean(True)  # Wrong type
        with pytest.raises(ValueError):
            OptionalInt("not an int")  # Wrong type

    def test_encode_decode(self):
        """Test encoding/decoding of Option values."""
        # Test with None
        opt_none = OptionalInt()
        encoded_none = opt_none.encode()
        decoded_none, size_none = OptionalInt.decode_from(encoded_none)
        assert isinstance(decoded_none, OptionalInt)
        assert decoded_none == None
        assert size_none == 1  # Tag byte

        # Test with value
        opt_value = OptionalInt(Int(42))
        encoded_value = opt_value.encode()
        decoded_value, size_value = OptionalInt.decode_from(encoded_value)
        assert isinstance(decoded_value, OptionalInt)
        assert decoded_value == Int(42)
        assert size_value > 1  # Tag byte + encoded value

    def test_equality(self):
        """Test equality comparison."""
        opt1 = OptionalInt()
        opt2 = OptionalInt()
        opt3 = OptionalInt(Int(42))
        opt4 = OptionalInt(Int(42))
        opt5 = OptionalInt(Int(43))
        opt6 = OptionalBoolean()

        # Same type, same value
        assert opt1 == opt2
        assert opt3 == opt4

        # Same type, different value
        assert opt1 != opt3
        assert opt3 != opt5

        # Different type, but same value
        assert opt1 == opt6

        # Compare with None
        assert opt1 == None  # noqa: E711
        assert opt3 != None  # noqa: E711

        # Compare with raw values
        assert opt3 == 42
        assert opt3 == Int(42)  # Option[Int](42) != Int(42)

    def test_buffer_operations(self):
        """Test buffer operations."""
        # Test with None
        opt_none = OptionalInt()
        assert opt_none.encode_size() == 1  # Just tag byte

        buffer = bytearray([0xFF] * 10)
        written = opt_none.encode_into(buffer, 5)
        assert written == 1
        assert buffer[5] == 0  # Tag byte for None

        # Test with value
        opt_value = OptionalInt(Int(42))
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
        opt_none = OptionalInt()
        opt_value = OptionalInt(Int(42))

        # Write None at offset 2
        opt_none.encode_into(buffer, 2)
        decoded_none, size_none = OptionalInt.decode_from(buffer=buffer, offset=2)
        assert isinstance(decoded_none, Option)
        assert decoded_none == None

        # Write Some at offset 5
        opt_value.encode_into(buffer, 5)
        decoded_value, size_value = OptionalInt.decode_from(buffer=buffer, offset=5)
        assert isinstance(decoded_value, Option)
        assert decoded_value == Int(42)

    def test_invalid_decode(self):
        """Test decoding invalid data."""
        # Invalid tag byte
        buffer = bytearray([0xFF])  # Invalid tag
        with pytest.raises(DecodeError):
            OptionalInt.decode_from(buffer=buffer)

        # Truncated buffer for Some value
        buffer = bytearray([1])  # Tag for Some but no value
        with pytest.raises(DecodeError):
            OptionalInt.decode_from(buffer=buffer)
