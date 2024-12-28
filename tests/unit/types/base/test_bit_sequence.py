"""Unit tests for bit sequence types."""

import pytest
from jam.types.base.bit_sequence import Bits, CoreBits
from jam.utils.constants import CORE_COUNT
from jam.utils.codec.composite.bit_sequences import BitSequence

class TestBitSequenceTypes:
    """Test suite for bit sequence type implementations."""

    @pytest.mark.parametrize("bit_length,bits", [
        (1, [True]),
        (2, [True, False]),
        (8, [True] * 8),
        (16, [False] * 16),
        (32, [True, False] * 16),
    ])
    def test_bits_creation(self, bit_length, bits):
        """Test creation of Bits with various lengths."""
        bit_seq = Bits(bit_length)
        assert bit_seq.bit_length == bit_length
        assert bit_seq.codec.bit_length == bit_length

    def test_core_bits_creation(self):
        """Test creation of CoreBits with CORE_COUNT length."""
        core_bits = CoreBits()
        assert core_bits.bit_length == CORE_COUNT
        assert core_bits.codec.bit_length == CORE_COUNT

    def test_bits_codec_roundtrip(self):
        """Test encoding and decoding roundtrip for Bits."""
        test_bits = [True, False, True, False]
        bit_seq = Bits(4)
        
        # Test encoding
        encoded = bit_seq.codec.encode(test_bits)
        
        # Test decoding
        decoded, size = bit_seq.codec.decode_from(encoded)
        assert decoded == test_bits
        assert size == len(encoded)

    def test_core_bits_codec_roundtrip(self):
        """Test encoding and decoding roundtrip for CoreBits."""
        test_bits = [True] * CORE_COUNT
        core_bits = CoreBits()
        
        # Test encoding
        encoded = core_bits.codec.encode(test_bits)
        
        # Test decoding
        decoded, size = core_bits.codec.decode_from(encoded)
        assert decoded == test_bits
        assert size == len(encoded)

    def test_invalid_bit_length(self):
        """Test that invalid bit lengths raise ValueError."""
        with pytest.raises(ValueError):
            Bits(-1)
        
        with pytest.raises(ValueError):
            Bits(0)

    def test_sequence_protocol(self):
        """Test that Bits implements the Sequence protocol correctly."""
        bits = Bits(4)
        test_sequence = [True, False, True, False]
        
        # Test length
        assert len(bits) == 4
        
        # Test iteration
        for bit in bits:
            assert isinstance(bit, bool)
            
        # Test indexing
        assert isinstance(bits[0], bool)
        
        # Test slicing
        assert isinstance(bits[1:3], list)

    def test_bits_equality(self):
        """Test equality comparison of Bits instances."""
        bits1 = Bits(4)
        bits2 = Bits(4)
        bits3 = Bits(8)
        
        assert bits1 == bits2
        assert bits1 != bits3
        
        core_bits1 = CoreBits()
        core_bits2 = CoreBits()
        assert core_bits1 == core_bits2

    def test_bits_repr(self):
        """Test string representation of Bits instances."""
        bits = Bits(4, [False, False, False, False])
        assert repr(bits) == f"Bits(bit_length={4}, bits={bits._bits})"
        
        core_bits = CoreBits([False] * CORE_COUNT)
        assert repr(core_bits) == f"Bits(bit_length={CORE_COUNT}, bits={core_bits._bits})" 