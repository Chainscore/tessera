"""Block and header types for the JAM protocol."""
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

import pytest

from jam.types.base import ByteArray32, ByteArray64, ByteArray96, ByteArray128, ByteArray144
from jam.types.base.integers.fixed import U32
from jam.utils.codec.base import Codable, codable_dataclass

TimeSlot = U32
ValidatorIndex = U32

@codable_dataclass()
@dataclass
class DemoHeader(Codable):
    """Block header structure."""
    parent: ByteArray32
    parent_state_root: ByteArray32
    extrinsic_hash: ByteArray32
    slot: TimeSlot
    author_index: ValidatorIndex
    entropy_source: ByteArray32
    seal: ByteArray32

class TestDemoHeader:
    """Test suite for DemoHeader type implementation."""

    @pytest.fixture
    def sample_header(self):
        """Create a sample DemoHeader for testing."""
        return DemoHeader(
            parent=ByteArray32(bytes(32)),
            parent_state_root=ByteArray32(bytes([1] * 32)),
            extrinsic_hash=ByteArray32(bytes([2] * 32)),
            slot=U32(123),
            author_index=U32(456),
            entropy_source=ByteArray32(bytes([5] * 32)),
            seal=ByteArray32(bytes([6] * 32))
        )

    def test_header_creation(self, sample_header):
        """Test creation of DemoHeader with valid values."""
        assert isinstance(sample_header.parent, ByteArray32)
        assert isinstance(sample_header.slot, U32)
        assert isinstance(sample_header.author_index, U32)

    def test_encoding_decoding(self, sample_header):
        """Test encoding and decoding of DemoHeader."""
        # Test encode_size
        size = sample_header.encode_size()
        assert size > 0

        # Test encode_into and decode_from
        buffer = bytearray(size)
        encoded_size = sample_header.encode_into(buffer)
        assert encoded_size == size

        decoded_header, decoded_size = DemoHeader.decode_from(bytes(buffer))
        
        # Verify decoded values match original
        assert decoded_header.parent == sample_header.parent
        assert decoded_header.parent_state_root == sample_header.parent_state_root
        assert decoded_header.extrinsic_hash == sample_header.extrinsic_hash
        assert decoded_header.slot == sample_header.slot
        assert decoded_header.author_index == sample_header.author_index
        assert decoded_header.entropy_source == sample_header.entropy_source
        assert decoded_header.seal == sample_header.seal
        assert decoded_size == size

    def test_enc_sequence(self, sample_header):
        """Test that enc_sequence returns all fields in correct order."""
        sequence = sample_header.enc_sequence()
        assert len(sequence) == 7  # Number of fields in DemoHeader
        assert sequence[0] == sample_header.parent
        assert sequence[1] == sample_header.parent_state_root
        assert sequence[2] == sample_header.extrinsic_hash
        assert sequence[3] == sample_header.slot
        assert sequence[4] == sample_header.author_index
        assert sequence[5] == sample_header.entropy_source
        assert sequence[6] == sample_header.seal
