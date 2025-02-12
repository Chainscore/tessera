"""Unit tests for Null type implementation."""

from jam.types.base.null import Null, Nullable
from jam.utils.codec.primitives.nulls import NullCodec

class TestNull:
    """Test suite for Null type."""

    def test_basic_null(self):
        """Test basic Null functionality."""
        null = Nullable()
        assert null.get() is None
        assert str(null) == "Null"
        assert repr(null) == "Null"

    def test_encode_decode(self):
        """Test encoding/decoding of Null values."""
        null = Nullable()
        encoded = null.encode()
        assert encoded == b""  # Null encodes to empty bytes
        
        decoded, size = Nullable.decode_from(buffer=encoded)
        assert isinstance(decoded, Nullable)
        assert decoded == null
        assert size == 0

    def test_equality(self):
        """Test equality comparison."""
        null1 = Nullable()
        null2 = Nullable()
        
        # Same type
        assert null1 == null2
        
        # Compare with None
        assert null1 == None  # noqa: E711
        
        # Compare with other types
        assert null1 != 42
        assert null1 != ""
        assert null1 != False
        assert null1 != []
        assert null1 != {}

    def test_buffer_operations(self):
        """Test buffer operations."""
        null = Nullable()
        
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
        decoded, size = Nullable.decode_from(buffer=buffer, offset=5)
        assert isinstance(decoded, Nullable)
        assert size == 0
        assert buffer == bytearray([0xFF] * 10)  # Buffer unchanged

    def test_codec(self):
        """Test that Null uses NullCodec."""
        null = Nullable()
        assert isinstance(null.codec, NullCodec)
        
        # Test that the codec is properly initialized
        assert null.codec.encode_size(None) == 0
        assert null.codec.encode(None) == b""
        
        # Test encode_into with codec
        buffer = bytearray([0xFF] * 10)
        written = null.codec.encode_into(None, buffer, 5)
        assert written == 0
        assert buffer == bytearray([0xFF] * 10)  # Buffer unchanged 