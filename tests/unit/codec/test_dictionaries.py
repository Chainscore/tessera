"""Unit tests for dictionary codec implementation."""

from typing import Any, Dict, List, Mapping, Tuple, Type, cast

import pytest

from jam.types.base.boolean import Boolean
from jam.types.base.integers import Int
from jam.types.base.string import String
from jam.utils.codec import Codable, DecodeError, EncodeError
from jam.utils.codec.composite.dictionaries import DictionaryCodec


def make_test_dict(
    key_type: Type[Codable], value_type: Type[Codable]
) -> Dict[Codable, Codable]:
    """Helper to create test dictionaries."""
    if key_type == String:
        keys = [String("a"), String("b"), String("c")]
    elif key_type == Int:
        keys = [Int(1), Int(2), Int(3)]
    else:
        raise ValueError(f"Unsupported key type: {key_type}")

    if value_type == Int:
        values: List[Int] = [Int(42), Int(43), Int(44)]
    elif value_type == Boolean:
        values: List[Boolean] = [Boolean(True), Boolean(False), Boolean(True)]
    elif value_type == String:
        values: List[String] = [String("x"), String("y"), String("z")]
    else:
        raise ValueError(f"Unsupported value type: {value_type}")

    return dict(zip(keys, values))


class TestDictionaryCodec:
    """Test suite for dictionary encoding/decoding."""

    def test_empty_dict(self):
        """Test encoding/decoding of empty dictionaries."""
        codec = DictionaryCodec()
        value: Dict[Codable, Codable] = {}
        encoded = codec.encode(value)
        # Should just be length byte (0)
        assert encoded == bytes([0])
        decoded, size = codec.decode_from(Codable, Codable, encoded)
        assert decoded == value
        assert size == 1

    @pytest.mark.parametrize(
        "key_type,value_type",
        [
            (String, Int),
            (Int, Boolean),
            (String, String),
            (Int, Int),
            (String, Boolean),
        ],
    )
    def test_various_types(self, key_type: Type[Codable], value_type: Type[Codable]):
        """Test dictionary codec with various key/value types."""
        codec = DictionaryCodec()
        sample = make_test_dict(key_type, value_type)
        encoded = codec.encode(cast(Mapping[Codable, Codable], sample))
        decoded, size = codec.decode_from(key_type, value_type, encoded)
        assert decoded == sample
        assert size == len(encoded)

    def test_deterministic_encoding(self):
        """Test that dictionary encoding is deterministic (same dict = same bytes)."""
        codec = DictionaryCodec()
        dict1 = {String("b"): Int(2), String("a"): Int(1), String("c"): Int(3)}
        dict2 = {String("a"): Int(1), String("c"): Int(3), String("b"): Int(2)}

        encoded1 = codec.encode(cast(Mapping[Codable, Codable], dict1))
        encoded2 = codec.encode(cast(Mapping[Codable, Codable], dict2))
        assert encoded1 == encoded2

        # Test with different insertion orders
        dict3: Dict[String, Int] = {}
        dict4: Dict[String, Int] = {}
        for k, v in [("c", 3), ("a", 1), ("b", 2)]:
            dict3[String(k)] = Int(v)
        for k, v in [("b", 2), ("c", 3), ("a", 1)]:
            dict4[String(k)] = Int(v)

        encoded3 = codec.encode(cast(Mapping[Codable, Codable], dict3))
        encoded4 = codec.encode(cast(Mapping[Codable, Codable], dict4))
        assert encoded3 == encoded4
        assert encoded3 == encoded1

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = DictionaryCodec()
        value = {String("a"): Int(1), String("b"): Int(2)}
        size = codec.encode_size(cast(Mapping[Codable, Codable], value))

        # Test encoding into too small buffer
        with pytest.raises(EncodeError):
            codec.encode_into(
                cast(Mapping[Codable, Codable], value), bytearray(size - 1)
            )

        # Test decoding from truncated buffer
        encoded = codec.encode(cast(Mapping[Codable, Codable], value))
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                codec.decode_from(String, Int, encoded[:i])

    @pytest.mark.parametrize(
        "invalid_value",
        [
            42,  # int
            "not a dict",  # str
            [1, 2, 3],  # list
            {1, 2, 3},  # set
            None,  # None
            True,  # bool
            b"bytes",  # bytes
        ],
    )
    def test_invalid_types(self, invalid_value: Any):
        """Test handling of invalid value types."""
        codec = DictionaryCodec()
        with pytest.raises(EncodeError):
            codec.encode(invalid_value)

    def test_invalid_key_value_types(self):
        """Test handling of invalid key/value types."""
        codec = DictionaryCodec()

        invalid_dicts = [
            {42: String("wrong")},  # non-Codable key
            {String("key"): "wrong"},  # non-Codable value
            {None: Int(1)},  # None key
            {String("key"): None},  # None value
            {True: String("wrong")},  # bool key
            {String("key"): [1, 2, 3]},  # list value
        ]

        for value in invalid_dicts:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        codec = DictionaryCodec()
        value = {String("a"): Int(1), String("b"): Int(2)}
        size = codec.encode_size(cast(Mapping[Codable, Codable], value))

        # Test encoding at different offsets
        for offset in [0, 1, 5]:
            # Create fresh buffer for each offset to avoid interference
            buffer = bytearray([0xFF] * (size + offset + 5))

            # Save original padding for verification
            prefix = buffer[:offset]
            suffix = buffer[offset + size :]

            # Perform encode/decode
            written = codec.encode_into(
                cast(Mapping[Codable, Codable], value), buffer, offset
            )
            assert written == size

            # Test decoding at same offset
            decoded, read = codec.decode_from(String, Int, buffer, offset)
            assert decoded == value
            assert read == size

            # Verify only the intended region was modified
            if offset + size < len(buffer):
                assert buffer[offset + size :] == suffix, "Suffix padding was modified"

    def test_string_key_values(self):
        """Test dictionaries with string keys and values with various content."""
        codec = DictionaryCodec()
        test_values = {
            String(""): String(""),  # Empty strings
            String("hello"): String("world"),  # ASCII
            String("🦀"): String("Rust"),  # Unicode
            String("key"): String("a" * 1000),  # Long string
            String("unicode"): String("Hello, 世界！"),  # Mixed ASCII and Unicode
        }

        encoded = codec.encode(cast(Mapping[Codable, Codable], test_values))
        decoded, size = codec.decode_from(String, String, encoded)
        assert decoded == test_values
        assert size == len(encoded)

    def test_duplicate_keys(self):
        """Test handling of duplicate keys during decoding."""
        codec = DictionaryCodec()
        # Create a buffer that would decode to duplicate keys
        buffer = bytes(
            [
                2,  # length
                1,  # first key (Int(1))
                42,  # first value (Int(42))
                1,  # duplicate key (Int(1))
                43,
            ]
        )  # second value (Int(43))

        with pytest.raises(DecodeError, match="Duplicate key"):
            codec.decode_from(Int, Int, buffer)

    def test_large_dictionary(self):
        """Test handling of large dictionaries."""
        codec = DictionaryCodec()
        # Create a large dictionary
        value = {String(str(i)): Int(i) for i in range(1000)}

        encoded = codec.encode(cast(Mapping[Codable, Codable], value))
        decoded, size = codec.decode_from(String, Int, encoded)
        assert decoded == value
        assert size == len(encoded)
