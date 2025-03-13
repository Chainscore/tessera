"""
Unit tests for array codec implementation.
"""

import pytest
from jam.types.base import Array
from jam.types.base.sequences.array import decodable_array
from jam.utils.codec.composite.arrays import ArrayCodec
from jam.utils.codec.errors import EncodeError, DecodeError
from jam.types.base.boolean import Boolean
from jam.types.base.string import String
from jam.types.base.integers import U8


class TestArrayCodec:
    """Test suite for array encoding/decoding."""

    def test_basic_integer_array(self):
        """Test basic encoding/decoding of integer arrays."""
        codec = ArrayCodec(3)
        value = [U8(1), U8(2), U8(3)]

        encoded = codec.encode(value)
        decoded, size = ArrayCodec.decode_from(3, U8, encoded)
        assert decoded == value
        assert size == len(encoded)

    @pytest.mark.parametrize(
        "codec,values",
        [
            (ArrayCodec(3), [U8(1), U8(2), U8(3)]),
            (ArrayCodec(2), [Boolean(True), Boolean(False)]),
            (ArrayCodec(2), [String("hello"), String("world")]),
        ],
    )
    def test_various_types(self, codec, values):
        """Test array codec with various element types."""
        encoded = codec.encode(values)
        decoded, size = ArrayCodec.decode_from(len(values), type(values[0]), encoded)
        assert decoded == values
        assert size == len(encoded)

    def test_empty_array(self):
        """Test handling of zero-length arrays."""
        codec = ArrayCodec(0)
        value = []

        encoded = codec.encode(value)
        decoded, size = ArrayCodec.decode_from(0, U8, encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_maximum_size(self):
        """Test array size limits."""
        # Test maximum allowed size
        codec = ArrayCodec(1024)
        assert codec.length == 1024

        # Test exceeding maximum size
        with pytest.raises(ValueError):
            ArrayCodec(1025)

    def test_negative_length(self):
        """Test that negative lengths are rejected."""
        with pytest.raises(ValueError):
            ArrayCodec(-1)

    def test_length_mismatch(self):
        """Test handling of incorrect array lengths."""
        codec = ArrayCodec(3)

        # Too few elements
        with pytest.raises(EncodeError):
            codec.encode([U8(1), U8(2)])

        # Too many elements
        with pytest.raises(EncodeError):
            codec.encode([U8(1), U8(2), U8(3), U8(4)])

    def test_invalid_element_type(self):
        """Test handling of invalid element types during encoding."""
        codec = ArrayCodec(3)

        with pytest.raises(EncodeError):
            codec.encode(["not", "a", "string"])  # type: ignore

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = ArrayCodec(3)
        value = [U8(1), U8(2), U8(3)]

        encoded = codec.encode(value)
        # Test decoding from too small buffer
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                ArrayCodec.decode_from(3, U8, encoded[:i])

    def test_nested_arrays(self):
        """Test encoding/decoding of nested arrays."""

        @decodable_array(3, U8)
        class FixedIntArray3(Array[U8]):
            pass

        @decodable_array(2, FixedIntArray3)
        class FixedIntArray2(Array[FixedIntArray3]):
            pass

        inner_array_1 = FixedIntArray3([U8(1), U8(2), U8(3)])
        inner_array_2 = FixedIntArray3([U8(4), U8(5), U8(6)])

        value = FixedIntArray2([inner_array_1, inner_array_2])
        encoded = value.encode()
        decoded, size = FixedIntArray2.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)
