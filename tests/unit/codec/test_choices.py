"""Unit tests for choice codec implementation."""

import pytest
from typing import Any, Tuple, Union, Optional, Type, List, cast, TypeVar

from jam.utils.codec.composite.choices import ChoiceCodec
from jam.types.base.choice import Choice
from jam.utils.codec.base import Codable, EncodeError, DecodeError
from jam.types.base.boolean import Boolean
from jam.types.base.integers.fixed import U16, U8
from jam.types.base.string import String

T = TypeVar('T')

class TestChoiceCodec:
    """Test suite for choice encoding/decoding."""

    def test_basic_choice(self):
        """Test basic encoding/decoding of choice values."""
        choice = Choice[Union[bool, int]]([Boolean, U8])
        value = Boolean(True)
        choice.set(value)
        encoded = choice.encode()
        decoded, size = Choice.decode_from([Boolean, U8], encoded)
        assert decoded == value
        assert size == len(encoded)

    @pytest.mark.parametrize("types,value", [
        ([Boolean, U8], Boolean(True)),
        ([Boolean, U8], U8(255)),
        ([String, U16, Boolean], U16(17)),
        ([String, U16, Boolean], String("test")),
        ([String, U16, Boolean], Boolean(False)),
    ], ids=lambda val: str(val) if not isinstance(val, list) else f"types_{len(val)}")
    def test_choice_variants(self, types: List[Type[Codable]], value: Codable):
        """Test encoding/decoding of different choice variants."""
        choice = Choice(types)
        choice.set(value)
        encoded = choice.encode()
        decoded, size = Choice.decode_from(types, encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_nested_choices(self):
        """Test encoding/decoding of nested choices."""
        class TestChoice(Choice[Union[bool, int]]):
            def __init__(self):
                super().__init__([Boolean, U8])
            
            @staticmethod
            def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Codable, int]:
                return ChoiceCodec.decode_from([Boolean, U8], buffer, offset)
                
        outer_types = [String, TestChoice]
        
        # Create nested choice structure
        inner_choice = TestChoice()
        inner_choice.set(U8(42))
        
        outer_choice = Choice(outer_types)
        outer_choice.set(inner_choice)
        
        encoded = outer_choice.encode()
        decoded, size = Choice.decode_from(outer_types, encoded)
        assert decoded == inner_choice.get()
        assert size == len(encoded)

    def test_invalid_tag(self):
        """Test handling of invalid choice tags during decoding."""
        types = [Boolean, U8]
        choice = Choice(types)
        
        # Create invalid encoding with out-of-bounds tag
        invalid_buffer = bytearray([2])  # Tag 2 is invalid for 2 choices
        
        with pytest.raises(DecodeError) as exc_info:
            Choice.decode_from(types, invalid_buffer)
        assert "Invalid choice tag" in str(exc_info.value)

    def test_type_mismatch(self):
        """Test handling of type mismatches."""
        types = [Boolean, U8]
        choice = Choice(types)
        
        # Try to set invalid type
        with pytest.raises(ValueError):
            choice.set(cast(Codable, String("invalid")))

    def test_empty_types(self):
        """Test handling of empty types list."""
        with pytest.raises(ValueError):
            Choice([])

    def test_unset_value(self):
        """Test handling of unset value."""
        choice = Choice([Boolean, U8])
        with pytest.raises(EncodeError) as exc_info:
            choice.encode()
        assert "Cannot encode None value" in str(exc_info.value)

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        types = [Boolean, U8]
        choice = Choice(types)
        choice.set(Boolean(True))
        
        encoded = choice.encode()
        # Test decoding from too small buffer
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                Choice.decode_from(types, encoded[:i])

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        types = [Boolean, U8]
        choice = Choice(types)
        choice.set(Boolean(True))
        
        # Test encoding at different offsets
        for offset in [0, 1, 5]:
            # Create fresh buffer for each offset
            buffer = bytearray([0xFF] * (choice.encode_size() + offset + 5))
            
            # Save original padding for verification
            suffix = buffer[offset + choice.encode_size():]
            
            # Perform encode/decode
            written = choice.encode_into(buffer, offset)
            assert written == choice.encode_size()
            
            # Test decoding at same offset
            decoded, read = Choice.decode_from(types, buffer, offset)
            assert decoded == Boolean(True)
            assert read == written
            
            # Verify only the intended region was modified
            if offset + written < len(buffer):
                assert buffer[offset + written:] == suffix, "Suffix padding was modified"

    @pytest.mark.parametrize("types,value,expected_size", [
        ([Boolean, U8], Boolean(True), 2),  # tag + bool
        ([Boolean, U8], U8(42), 2),         # tag + u8
        ([String, U8], String("test"), 6),  # tag + string length + string
        ([U16, U8], U16(1000), 3),          # tag + u16
    ], ids=lambda val: str(val) if not isinstance(val, list) else f"types_{len(val)}")
    def test_encode_size(self, types: List[Type[Codable]], value: Codable, expected_size: int):
        """Test that encode_size returns correct sizes for different choices."""
        choice = Choice(types)
        choice.set(value)
        assert choice.encode_size() == expected_size
        assert len(choice.encode()) == expected_size

    def test_deterministic_encoding(self):
        """Test that choice encoding is deterministic."""
        types = [Boolean, U8]
        choice1 = Choice(types)
        choice2 = Choice(types)
        
        value = Boolean(True)
        choice1.set(value)
        choice2.set(value)
        
        assert choice1.encode() == choice2.encode()

    def test_get_unset_value(self):
        """Test getting value when none has been set."""
        choice = Choice([Boolean, U8])
        assert choice.get() is None

    def test_equality(self):
        """Test equality comparison."""
        types = [Boolean, U8]
        choice1 = Choice(types)
        choice2 = Choice(types)
        choice3 = Choice(types)
        
        value1 = Boolean(True)
        value2 = U8(42)
        
        choice1.set(value1)
        choice2.set(value1)
        choice3.set(value2)
        
        assert choice1 == choice2
        assert choice1 != choice3
        assert choice1 != "not a choice"

    def test_string_representation(self):
        """Test string representation."""
        choice = Choice([Boolean, U8])
        assert str(choice) == "Choice(None)"
        
        choice.set(Boolean(True))
        assert str(choice) == "Choice(Boolean(True))"
