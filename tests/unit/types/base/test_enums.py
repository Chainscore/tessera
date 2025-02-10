"""Unit tests for enum type implementation."""

import pytest
from jam.types.base.enum import Enum, decodable_enum
from jam.utils.codec.errors import DecodeError
from jam.utils.json.serde import JsonDeserializationError


@decodable_enum
class TestEnum(Enum):
    """Test enum class."""
    A = "a"
    B = "b"
    C = "c"

@decodable_enum
class LargeEnum(Enum):
    """Test enum with many values."""
    V0 = 0
    V1 = 1
    V2 = 2
    V3 = 3
    V4 = 4
    V5 = 5
    V6 = 6
    V7 = 7
    V8 = 8
    V9 = 9
    V10 = 10
    V11 = 11
    V12 = 12
    V13 = 13
    V14 = 14
    V15 = 15
    V16 = 16
    V17 = 17

class TestEnumTypes:
    """Test suite for enum type implementations."""

    def test_basic_enum(self):
        """Test basic enum functionality."""
        assert TestEnum.A == TestEnum("a")
        assert TestEnum.B == TestEnum("b")
        assert TestEnum.C == TestEnum("c")

        assert TestEnum.A.name == "A"
        assert TestEnum.B.name == "B"
        assert TestEnum.C.name == "C"

    def test_enum_codec_roundtrip(self):
        """Test encoding and decoding roundtrip."""
        for value in TestEnum:
            encoded = value.encode()
            decoded, size = TestEnum.decode_from(encoded)
            assert decoded == value
            assert size == 1  # Should always be 1 byte

    def test_enum_json_serialization(self):
        """Test JSON serialization/deserialization."""
        # Test from_json with value
        assert TestEnum.from_json("a") == TestEnum.A
        assert TestEnum.from_json("b") == TestEnum.B
        assert TestEnum.from_json("c") == TestEnum.C

        # Test from_json with name
        assert TestEnum.from_json("A") == TestEnum.A
        assert TestEnum.from_json("B") == TestEnum.B
        assert TestEnum.from_json("C") == TestEnum.C

        # Test to_json
        assert TestEnum.A.to_json() == "a"
        assert TestEnum.B.to_json() == "b"
        assert TestEnum.C.to_json() == "c"

    def test_invalid_json_values(self):
        """Test handling of invalid JSON values."""
        with pytest.raises(JsonDeserializationError):
            TestEnum.from_json("invalid")
        with pytest.raises(JsonDeserializationError):
            TestEnum.from_json(42)
        with pytest.raises(JsonDeserializationError):
            TestEnum.from_json(None)

    def test_encode_size(self):
        """Test encode_size returns correct value."""
        assert TestEnum.A.encode_size() == 1
        assert TestEnum.B.encode_size() == 1
        assert TestEnum.C.encode_size() == 1

    def test_buffer_operations(self):
        """Test buffer encoding/decoding operations."""
        # Test encoding into buffer
        buffer = bytearray([0xFF] * 3)
        written = TestEnum.A.encode_into(buffer, 1)
        assert written == 1
        assert buffer[0] == 0xFF  # Unchanged
        assert buffer[2] == 0xFF  # Unchanged

        # Test decoding from buffer with offset
        decoded, size = TestEnum.decode_from(buffer, 1)
        assert decoded == TestEnum.A
        assert size == 1

    def test_enum_comparison(self):
        """Test enum comparison operations."""
        assert TestEnum.A == TestEnum.A
        assert TestEnum.A != TestEnum.B
        assert TestEnum.A != "A"
        assert TestEnum.A != 1

    def test_invalid_buffer_decode(self):
        """Test decoding from invalid buffer."""
        # Empty buffer
        with pytest.raises(DecodeError):
            TestEnum.decode_from(bytes([]))

        # Invalid index
        with pytest.raises(IndexError):
            TestEnum.decode_from(bytes([99]))  # Index out of range

    def test_decorator_functionality(self):
        """Test that decodable_enum decorator adds required methods."""
        assert hasattr(TestEnum, 'decode_from')
        assert callable(TestEnum.decode_from)