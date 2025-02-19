"""Unit tests for choice codec implementation."""

import pytest
from typing import Type, List, TypeVar

from jam.types.base.choices import Choice, decodable_choice
from jam.utils.codec.codable import Codable
from jam.utils.codec import EncodeError, DecodeError
from jam.types.base.boolean import Boolean
from jam.types.base.integers.fixed import U16, U8
from jam.types.base.string import String

T = TypeVar("T")


class TestChoiceCodec:
    """Test suite for choice encoding/decoding."""

    def test_basic_choice(self):
        """Test basic encoding/decoding of choice values."""

        @decodable_choice
        class BoolIntChoice(Choice):
            A: Boolean
            B: U8

        value = Boolean(True)
        choice = BoolIntChoice(value)
        encoded = choice.encode()
        decoded, size = BoolIntChoice.decode_from(encoded)
        assert decoded.value == {"A": value}
        assert size == len(encoded)

    @pytest.mark.parametrize(
        "types,value",
        [
            ([Boolean, U8], Boolean(True)),
            ([Boolean, U8], U8(255)),
            ([String, U16], U16(17)),
            ([String, U16], String("test")),
            ([String, Boolean], Boolean(False)),
        ],
        ids=lambda val: str(val) if not isinstance(val, list) else f"types_{len(val)}",
    )
    def test_choice_variants(self, types: List[Type[Codable]], value: Codable):
        """Test encoding/decoding of different choice variants."""

        @decodable_choice
        class CustomChoice(Choice):
            A: types[0]
            B: types[1]

        choice = CustomChoice(value)
        encoded = choice.encode()
        decoded, size = CustomChoice.decode_from(encoded)
        assert list(decoded.value.values())[0] == value
        assert size == len(encoded)

    def test_nested_choices(self):
        """Test encoding/decoding of nested choices."""

        @decodable_choice
        class TestChoice(Choice):
            A: String
            B: U8

        @decodable_choice
        class OuterChoice(Choice):
            A: String
            B: TestChoice

        # Create nested choice structure
        inner_choice = TestChoice(U8(42))
        outer_choice = OuterChoice(inner_choice)
        encoded = outer_choice.encode()
        decoded, size = OuterChoice.decode_from(encoded)
        assert list(decoded.value.values())[0] == inner_choice
        assert size == len(encoded)

    def test_invalid_tag(self):
        """Test handling of invalid choice tags during decoding."""

        @decodable_choice
        class TestChoice(Choice):
            A: Boolean
            B: U8

        # Create invalid encoding with out-of-bounds tag
        invalid_buffer = bytearray([2])  # Tag 2 is invalid for 2 choices

        with pytest.raises(DecodeError) as exc_info:
            TestChoice.decode_from(invalid_buffer)
        assert "Invalid choice tag" in str(exc_info.value)

    def test_type_mismatch(self):
        """Test handling of type mismatches."""

        @decodable_choice
        class TestChoice(Choice):
            A: Boolean
            B: U8

        # Try to create choice with invalid type
        with pytest.raises(ValueError):
            TestChoice(String("invalid"))

    def test_empty_types(self):
        """Test handling of empty types list."""
        with pytest.raises(ValueError):

            @decodable_choice
            class EmptyChoice(Choice):
                ...

    def test_unset_value(self):
        """Test handling of unset value."""

        @decodable_choice
        class TestChoice(Choice):
            A: Boolean
            B: U8

        with pytest.raises(ValueError):
            choice = TestChoice(None)  # type: ignore

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""

        @decodable_choice
        class TestChoice(Choice):
            A: Boolean
            B: U8

        choice = TestChoice(Boolean(True))
        encoded = choice.encode()

        # Test decoding from too small buffer
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                TestChoice.decode_from(encoded[:i])

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""

        @decodable_choice
        class TestChoice(Choice):
            A: Boolean
            B: U8

        choice = TestChoice(Boolean(True))

        # Test encoding at different offsets
        for offset in [0, 1, 5]:
            # Create fresh buffer for each offset
            buffer = bytearray([0xFF] * (choice.encode_size() + offset + 5))

            # Save original padding for verification
            suffix = buffer[offset + choice.encode_size() :]

            # Perform encode/decode
            written = choice.encode_into(buffer, offset)
            assert written == choice.encode_size()

            # Test decoding at same offset
            decoded, read = TestChoice.decode_from(buffer, offset)
            assert list(decoded.value.values())[0] == Boolean(True)
            assert read == written

            # Verify only the intended region was modified
            if offset + written < len(buffer):
                assert (
                    buffer[offset + written :] == suffix
                ), "Suffix padding was modified"

    @pytest.mark.parametrize(
        "value,expected_size",
        [
            (Boolean(True), 2),  # tag + bool
            (U8(42), 2),  # tag + u8
        ],
        ids=str,
    )
    def test_encode_size(self, value: Codable, expected_size: int):
        """Test that encode_size returns correct sizes for different choices."""

        @decodable_choice
        class TestChoice(Choice):
            A: Boolean
            B: U8

        choice = TestChoice(value)
        assert choice.encode_size() == expected_size
        assert len(choice.encode()) == expected_size

    def test_deterministic_encoding(self):
        """Test that choice encoding is deterministic."""

        @decodable_choice
        class TestChoice(Choice):
            A: Boolean
            B: U8

        choice1 = TestChoice(Boolean(True))
        choice2 = TestChoice(Boolean(True))

        assert choice1.encode() == choice2.encode()

    def test_equality(self):
        """Test equality comparison."""

        @decodable_choice
        class TestChoice(Choice):
            A: Boolean
            B: U8

        choice1 = TestChoice(Boolean(True))
        choice2 = TestChoice(Boolean(True))
        choice3 = TestChoice(U8(42))

        assert choice1 == choice2
        assert choice1 != choice3
        assert choice1 != "not a choice"

    def test_string_representation(self):
        """Test string representation."""

        @decodable_choice
        class TestChoice(Choice):
            A: Boolean
            B: U8

        choice = TestChoice(Boolean(True))
        assert str(choice) == "TestChoice({'A': " + str(Boolean(True)) + "})"
