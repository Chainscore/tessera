"""
Unit tests for tuple codec implementation.
"""

import pytest
from typing import Tuple as PyTuple
from jam.core.codec.composite.tuples import (
    Tuple, TupleCodec, make_tuple_codec, register_tuple_type,
    EncodeError, DecodeError
)

class TestTupleCodec:
    """Test suite for tuple encoding/decoding."""

    def test_basic_tuple(self):
        """Test basic encoding/decoding of simple tuples."""
        codec = TupleCodec([int, str, bool])
        value = (42, "hello", True)
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)
        assert size == codec.encode_size(value)

    @pytest.mark.parametrize("types,value", [
        ((int,), (42,)),
        ((int, str), (42, "hello")),
        ((bool, int, str), (True, 42, "hello")),
        ((str, bool, int, str), ("test", False, 42, "end")),
    ])
    def test_various_tuple_sizes(self, types, value):
        """Test tuples of different sizes."""
        codec = TupleCodec(types)
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_empty_tuple(self):
        """Test handling of empty tuples."""
        codec = TupleCodec([])
        value = ()
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value
        assert size == 0
        assert size == len(encoded)
        assert size == codec.encode_size(value)

    def test_nested_tuples(self):
        """Test encoding/decoding of nested tuples."""
        # Create a codec for Tuple[Tuple[int, str], bool]
        inner_codec = TupleCodec([int, str])
        outer_codec = TupleCodec([PyTuple[int, str], bool])
        
        value = ((42, "hello"), True)
        encoded = outer_codec.encode(value)
        decoded, size = outer_codec.decode_from(encoded)
        assert decoded == value
        assert size == len(encoded)

    def test_length_mismatch(self):
        """Test handling of incorrect tuple lengths."""
        codec = TupleCodec([int, str, bool])
        
        # Too few elements
        with pytest.raises(EncodeError):
            codec.encode((42, "hello"))
            
        # Too many elements
        with pytest.raises(EncodeError):
            codec.encode((42, "hello", True, False))

    def test_type_mismatch(self):
        """Test handling of incorrect element types."""
        codec = TupleCodec([int, str, bool])
        
        invalid_tuples = [
            ("not int", "hello", True),  # Wrong first element type
            (42, True, True),            # Wrong second element type
            (42, "hello", "not bool"),   # Wrong third element type
        ]
        
        for value in invalid_tuples:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_invalid_input_type(self):
        """Test handling of non-tuple inputs."""
        codec = TupleCodec([int, str])
        
        invalid_inputs = [
            42,             # int
            "hello",        # str
            [42, "hello"],  # list
            {42, "hello"},  # set
        ]
        
        for value in invalid_inputs:
            with pytest.raises(EncodeError):
                codec.encode(value)

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = TupleCodec([int, str])
        value = (42, "hello")
        size = codec.encode_size(value)
        
        # Test encoding into too small buffer
        with pytest.raises(EncodeError):
            codec.encode_into(value, bytearray(size - 1))
            
        # Test decoding from too small buffer
        encoded = codec.encode(value)
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                codec.decode_from(encoded[:i])

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        codec = TupleCodec([int, str])
        value = (42, "hello")
        size = codec.encode_size(value)
        
        # Create buffer with padding
        buffer = bytearray([0xFF] * (size + 2))
        
        # Test encoding at offset
        written = codec.encode_into(value, buffer, 1)
        assert written == size
        
        # Test decoding at offset
        decoded, read = codec.decode_from(buffer, 1)
        assert decoded == value
        assert read == size
        
        # Verify padding wasn't overwritten
        assert buffer[0] == 0xFF
        assert buffer[-1] == 0xFF

    def test_tuple_constructors(self):
        """Test different ways of creating tuple codecs."""
        value = (42, "hello")
        
        # Using Tuple type syntax
        codec1 = TupleCodec([int, str])
        
        # Using make_tuple_codec function
        codec2 = make_tuple_codec(int, str)
        
        # Using TupleCodec constructor
        codec3 = TupleCodec([int, str])
        
        # All should produce identical results
        encoded1 = codec1.encode(value)
        encoded2 = codec2.encode(value)
        encoded3 = codec3.encode(value)
        
        assert encoded1 == encoded2 == encoded3

    def test_registry_integration(self):
        """Test integration with codec registry."""
        from jam.core.codec.base import CodecRegistry
        
        # Register tuple type
        tuple_type = PyTuple[int, str]
        register_tuple_type(tuple_type)
        
        # Test encoding through registry
        value = (42, "hello")
        codec = CodecRegistry.get(tuple_type)
        assert codec is not None
        
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value

    def test_complex_types(self):
        """Test tuples with complex element types."""
        from jam.core.codec.composite.options import Option
        from jam.core.codec.composite.arrays import Array
        
        # Create codec for Tuple[Option[int], Array[str, 2]]
        codec = TupleCodec([Option[int], Array[str, 2]])
        
        value = (42, ("hello", "world"))
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value

    def test_tuple_with_empty_string(self):
        """Test handling of empty strings in tuples."""
        codec = TupleCodec([str, int, str])
        value = ("", 42, "hello")
        encoded = codec.encode(value)
        decoded, size = codec.decode_from(encoded)
        assert decoded == value

    def test_partial_decode_failure(self):
        """Test handling of decode failures partway through tuple."""
        codec = TupleCodec([int, str])
        
        # Create valid encoding and corrupt it
        valid = codec.encode((42, "hello"))
        corrupted = valid[:-1]  # Remove last byte
        
        with pytest.raises(DecodeError) as exc_info:
            codec.decode_from(corrupted)
        assert "Failed to decode tuple element" in str(exc_info.value)

    @pytest.mark.parametrize("types,expected_error", [
        ((int, "not a type"), TypeError),
        ((list,), ValueError),  # No codec for raw list type
        ((dict,), ValueError),  # No codec for raw dict type
    ])
    def test_invalid_type_specifications(self, types, expected_error):
        """Test handling of invalid type specifications."""
        with pytest.raises(expected_error):
            Tuple[types]