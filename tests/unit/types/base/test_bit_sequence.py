"""Unit tests for bit sequence types."""

import pytest
from jam.types.base.bit import Bit
from jam.types.base.boolean import Boolean
from jam.types.base.sequences import BitArray, decodable_bit_array
from jam.utils.constants import CORE_COUNT

@decodable_bit_array(4)  # Fixed length for testing
class TestBits(BitArray): ...

@decodable_bit_array(CORE_COUNT)  # Fixed length for testing
class CoreBits(BitArray): ...

class TestBitSequenceTypes:
    """Test suite for bit sequence type implementations."""

    @pytest.mark.parametrize("bit_length,bits", [
        (1, [True]),
        (2, [True, False]),
        # (8, [True] * 8),
        # (16, [False] * 16),
        # (32, [True, False] * 16),
    ])
    def test_bits_creation(self, bit_length, bits):
        """Test creation of Bits with various lengths."""

        @decodable_bit_array(bit_length)
        class NBits(BitArray): ...
        
        bit_seq = NBits(bits)
        assert len(bit_seq) == bit_length
        for i, bit in enumerate(bit_seq):
            assert bit.value == bits[i]

    def test_core_bits_creation(self):
        """Test creation of CoreBits with CORE_COUNT length."""
        core_bits = CoreBits([Bit(True)] * CORE_COUNT)
        assert len(core_bits) == CORE_COUNT
        assert all(bit.value for bit in core_bits)

    def test_bits_codec_roundtrip(self):
        """Test encoding and decoding roundtrip for Bits."""
        test_bits = [Boolean(True), Boolean(False), Boolean(True), Boolean(False)]
        bit_seq = TestBits(test_bits)
        encoded = bit_seq.encode()
        decoded, size = TestBits.decode_from(encoded)
        assert list(decoded) == test_bits
        assert size == len(encoded)

    def test_core_bits_codec_roundtrip(self):
        """Test encoding and decoding roundtrip for CoreBits."""
        test_bits = [Boolean(True)] * CORE_COUNT
        core_bits = CoreBits(test_bits)
        encoded = core_bits.encode()
        decoded, size = CoreBits.decode_from(encoded)
        assert list(decoded) == test_bits
        assert size == len(encoded)

    def test_sequence_protocol(self):
        """Test that Bits implements the Sequence protocol correctly."""
        test_bits = TestBits([Boolean(True), Boolean(False), Boolean(True), Boolean(False)])
        
        # Test length
        assert len(test_bits) == 4
        
        # Test iteration
        assert all(isinstance(bit, Bit) for bit in test_bits)
            
        # Test indexing
        assert isinstance(test_bits[0], Bit)
        
        # Test slicing
        sliced = test_bits[1:3]
        assert isinstance(sliced, list)
        assert sliced == [False, True]

    def test_bits_equality(self):
        """Test equality comparison of Bits instances."""
        bits1 = TestBits([Boolean(True), Boolean(False), Boolean(True), Boolean(False)])
        bits2 = TestBits([Boolean(True), Boolean(False), Boolean(True), Boolean(False)])
        bits3 = TestBits([Boolean(True), Boolean(True), Boolean(True), Boolean(True)])
        
        assert bits1 == bits2
        assert bits1 != bits3
        
        core_bits1 = CoreBits([Boolean(True)] * CORE_COUNT)
        core_bits2 = CoreBits([Boolean(True)] * CORE_COUNT)
        assert core_bits1 == core_bits2

    def test_bits_repr(self):
        """Test string representation of Bits instances."""
        bits = TestBits([Boolean(False), Boolean(False), Boolean(False), Boolean(False)])
        assert repr(bits) == "TestBits([Bit(0), Bit(0), Bit(0), Bit(0)])"
        
        core_bits = CoreBits([Boolean(False)] * CORE_COUNT)
        assert repr(core_bits) == f"CoreBits({[Bit(False)] * CORE_COUNT})"

    def test_invalid_bits(self):
        """Test that invalid bit values raise appropriate errors."""            
        with pytest.raises(TypeError):
            TestBits([True, -1, False, True])  # type: ignore
            
        with pytest.raises(TypeError):
            bits = TestBits([Boolean(True), Boolean(False), Boolean(True), Boolean(False)])
            bits[0] = 2  # type: ignore