"""Unit tests for bit sequence types."""

import pytest
from jam.types.base.bit_sequence import Bits
from jam.types.extended.core_bits import CoreBits
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
        bit_seq = Bits(bits)
        assert len(bit_seq) == bit_length

    def test_core_bits_creation(self):
        """Test creation of CoreBits with CORE_COUNT length."""
        core_bits = CoreBits([True] * CORE_COUNT)
        assert len(core_bits) == CORE_COUNT

    def test_bits_codec_roundtrip(self):
        """Test encoding and decoding roundtrip for Bits."""
        test_bits = [True, False, True, False]
        bit_seq = Bits(test_bits)
        
        # Test encoding
        encoded = bit_seq.codec.encode(test_bits)
        
        # Test decoding
        decoded, size = Bits.decode_from(len(test_bits), encoded)
        assert decoded == test_bits
        assert size == len(encoded)

    def test_core_bits_codec_roundtrip(self):
        """Test encoding and decoding roundtrip for CoreBits."""
        test_bits = [True] * CORE_COUNT
        core_bits = CoreBits(test_bits)
        
        # Test encoding
        encoded = core_bits.codec.encode(test_bits)
        
        # Test decoding
        decoded, size = CoreBits.decode_from(encoded)
        assert decoded == test_bits
        assert size == len(encoded)

    def test_sequence_protocol(self):
        """Test that Bits implements the Sequence protocol correctly."""
        bits = Bits([True, False, True, False])
        
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
        bits1 = Bits([True, False, True, False])
        bits2 = Bits([True, False, True, False])
        bits3 = Bits([True] * 8)
        
        assert bits1 == bits2
        assert bits1 != bits3
        
        core_bits1 = CoreBits([True] * CORE_COUNT)
        core_bits2 = CoreBits([True] * CORE_COUNT)
        assert core_bits1 == core_bits2

    def test_bits_repr(self):
        """Test string representation of Bits instances."""
        bits = Bits([False, False, False, False])
        assert repr(bits) == f"Bits(bits={bits._bits})"
        
        core_bits = CoreBits([False] * CORE_COUNT)
        assert repr(core_bits) == f"Bits(bits={core_bits._bits})" 