"""Unit tests for string type implementation."""

import pytest
from jam.types.base.string import String
from jam.utils.codec.errors import DecodeError

class TestString:
    def test_initialization(self):
        """Test String initialization."""
        # Valid cases
        assert String("hello").value == "hello"
        assert String("").value == ""  # Empty string
        assert String("🌟").value == "🌟"  # Unicode
        
        # Invalid cases
        with pytest.raises(TypeError):
            String(123)  # type: ignore
        with pytest.raises(TypeError):
            String(b"bytes")  # type: ignore
        with pytest.raises(TypeError):
            String(None)  # type: ignore

    def test_protocol_methods(self):
        """Test Python protocol methods."""
        s = String("hello world")
        
        # __str__
        assert str(s) == "hello world"
        
        # __len__
        assert len(s) == 11
        
        # __getitem__
        assert s[0] == "h"
        assert s[-1] == "d"
        assert s[1:5] == "ello"
        
        # __contains__
        assert "hello" in s
        assert "xyz" not in s
        
        # __eq__
        assert s == String("hello world")
        assert s == "hello world"
        assert s != String("different")
        assert s != 123
        
        # __hash__
        d = {s: "test"}
        assert d[String("hello world")] == "test"
        
        # __add__
        assert String("hello") + String(" world") == String("hello world")
        assert String("hello") + " world" == String("hello world")
        
        # __repr__
        assert repr(s) == 'String("hello world")'

    def test_unicode_handling(self):
        """Test handling of Unicode strings."""
        s = String("Hello 🌟 World")
        
        # Length is 13 because the emoji is 2 code units
        assert len(s) == 13
        assert s[6:7] == "🌟"  # Emoji takes 2 indices
        assert "🌟" in s
        
        # Test other Unicode characters
        s2 = String("café")  # é is a single code unit
        assert len(s2) == 4
        assert s2[3] == "é"
        
        s3 = String("Hello 世界")  # CJK characters are single code units
        assert len(s3) == 8
        assert s3[6:8] == "世界"

    def test_codec(self):
        """Test encoding/decoding."""
        test_cases = [
            "",  # Empty string
            "hello",  # ASCII
            "Hello 世界",  # Mixed ASCII and Unicode
            "🌟✨🌙",  # All Unicode
            "a" * 1000,  # Long string
            "café",  # Latin-1 characters
            "Hello\u0000World",  # Null bytes
            "\u0001\u001F",  # Control characters
        ]
        
        for text in test_cases:
            s = String(text)
            encoded = s.encode()
            decoded, size = String.decode_from(encoded)
            
            assert isinstance(decoded, String)
            assert decoded == s
            assert decoded.value == text
            assert size == len(encoded)

    def test_empty_string(self):
        """Test empty string handling."""
        s = String("")
        assert len(s) == 0
        assert str(s) == ""
        
        encoded = s.encode()
        decoded, size = String.decode_from(encoded)
        assert decoded == s
        assert size > 0  # Should include length prefix

    def test_error_cases(self):
        """Test error handling."""
        s = String("test")
        encoded = s.encode()
        
        # Truncated buffer
        with pytest.raises(DecodeError):
            String.decode_from(encoded[:-1])
            
        # Invalid UTF-8
        with pytest.raises(DecodeError):
            String.decode_from(b"\x01\xFF")  # Invalid UTF-8 byte 