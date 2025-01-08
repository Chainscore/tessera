"""
Unit tests for bit sequence codec implementation.
"""

from typing import Optional, Sequence, Union
import pytest
from jam.types.base import BitSequence, decodable_bit_sequence
from jam.utils.codec.composite.bit_sequences import BitSequenceCodec, EncodeError, DecodeError

class TestBitSequenceCodec:
    """Test suite for bit sequence encoding/decoding."""
    
    @pytest.mark.parametrize("bit_length,bits", [
        (0, []),                      # Empty sequence
        (1, [True]),                  # Single bit
        (1, [False]),                 # Single bit
        (2, [True, False]),          # Two bits
        (3, [True, False, True]),    # Three bits
        (8, [False] * 8),           # Full byte
        (8, [True] * 8),            # Full byte
        (8, [True] * 7 + [False]),  # Full byte mixed
        (9, [True] * 9),            # More than one byte
        (16, [False] * 16),         # Two full bytes
        (16, [True, False] * 8),    # Alternating pattern
    ])
    def test_codec_roundtrip(self, bit_length, bits):
        """Test encoding and decoding roundtrip for valid values."""
        
        @decodable_bit_sequence(bit_length)
        class NBits(BitSequence): pass
                
        bit_seq = NBits(bits)
        encoded = bit_seq.encode()
        decoded, size = NBits.decode_from(encoded)
        assert list(decoded) == bits
        assert size == len(encoded)
        assert size == bit_seq.encode_size()

    def test_length_mismatch(self):
        """Test that sequences with wrong length raise appropriate errors."""
        codec = BitSequenceCodec(8)
        
        # Too few bits
        with pytest.raises(EncodeError) as exc_info:
            codec.encode([True] * 7)
        assert "length mismatch" in str(exc_info.value)
            
        # Too many bits
        with pytest.raises(EncodeError) as exc_info:
            codec.encode([True] * 9)
        assert "length mismatch" in str(exc_info.value)

    def test_byte_alignment(self):
        """Test that bits are correctly packed into bytes."""
        codec = BitSequenceCodec(8)
        
        # Test sequence: [1,0,1,0,1,0,1,0] should encode to 0x55
        bits = [True, False] * 4
        encoded = codec.encode(bits)
        assert len(encoded) == 1
        assert encoded[0] == 0x55

        # Test sequence: [1,1,1,1,0,0,0,0] should encode to 0x0F
        bits = [True] * 4 + [False] * 4
        encoded = codec.encode(bits)
        assert len(encoded) == 1
        assert encoded[0] == 0x0F

    @pytest.mark.parametrize("bit_length,expected_size", [
        (0, 0),       # Empty sequence
        (1, 1),       # Single bit
        (7, 1),       # 7 bits
        (8, 1),       # Full byte
        (9, 2),       # Just over one byte
        (15, 2),      # 15 bits
        (16, 2),      # Two full bytes
        (17, 3),      # Just over two bytes
    ])
    def test_encode_size(self, bit_length, expected_size):
        """Test that encode_size returns correct sizes for different lengths."""
        codec = BitSequenceCodec(bit_length)
        bits = [True] * bit_length
        assert codec.encode_size(bits) == expected_size

    def test_buffer_bounds(self):
        """Test buffer bounds checking."""
        codec = BitSequenceCodec(16)
        bits = [True] * 16
        
        # Test encoding into too small buffer
        with pytest.raises(EncodeError):
            codec.encode_into(bits, bytearray(1))
        
        # Test decoding from too small buffer
        encoded = codec.encode(bits)
        for i in range(len(encoded)):
            with pytest.raises(DecodeError):
                codec.decode_from(length=16, buffer=encoded[:i], offset=0)

    def test_offset_handling(self):
        """Test encoding and decoding with buffer offsets."""
        codec = BitSequenceCodec(8)
        bits = [True] * 8
        
        # Create buffer with padding
        buffer = bytearray([0xFF] * 3)
        
        # Test encoding at offset
        written = codec.encode_into(bits, buffer, 1)
        assert written == 1
        assert buffer[0] == 0xFF  # Padding unchanged
        assert buffer[2] == 0xFF  # Padding unchanged
        
        # Test decoding at offset
        decoded, size = codec.decode_from(length=len(bits), buffer=buffer, offset=1)
        assert list(decoded) == bits
        assert size == 1

    def test_bit_ordering(self):
        """Test that bits are ordered correctly within bytes."""
        codec = BitSequenceCodec(8)
        
        # Test pattern [1,0,0,0,0,0,0,0] should encode to 0x01 (LSB first)
        bits = [True] + [False] * 7 
        encoded = codec.encode(bits)
        assert encoded[0] == 0x01

        # Test pattern [0,0,0,0,0,0,0,1] should encode to 0x80 (LSB first)
        bits = [False] * 7 + [True]
        encoded = codec.encode(bits)
        assert encoded[0] == 0x80 