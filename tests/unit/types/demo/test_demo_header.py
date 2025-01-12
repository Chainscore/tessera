"""Block and header types for the JAM protocol."""
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple
import json

import pytest

from jam.types.base import ByteArray32, ByteArray64, ByteArray96, ByteArray128, ByteArray144
from jam.types.base.integers.fixed import U32
from jam.utils.codec import Codable, decodable_dataclass

TimeSlot = U32
ValidatorIndex = U32

@decodable_dataclass
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

    def test_json_serialization(self, sample_header):
        """Test JSON serialization and deserialization."""
        # Test to_json
        json_data = sample_header.to_json()
        assert isinstance(json_data, dict)
        
        # Verify ByteArray32 fields are hex strings
        assert isinstance(json_data['parent'], str)
        assert json_data['parent'].startswith('0x')
        assert isinstance(json_data['parent_state_root'], str)
        assert json_data['parent_state_root'].startswith('0x')
        assert isinstance(json_data['extrinsic_hash'], str)
        assert json_data['extrinsic_hash'].startswith('0x')
        
        # Verify integer fields
        assert json_data['slot'] == 123
        assert json_data['author_index'] == 456
        
        # Verify remaining ByteArray32 fields
        assert isinstance(json_data['entropy_source'], str)
        assert json_data['entropy_source'].startswith('0x')
        assert isinstance(json_data['seal'], str)
        assert json_data['seal'].startswith('0x')

        # Test from_json
        deserialized_header = DemoHeader.from_json(json_data)
        assert isinstance(deserialized_header, DemoHeader)
        assert deserialized_header.parent == sample_header.parent
        assert deserialized_header.parent_state_root == sample_header.parent_state_root
        assert deserialized_header.extrinsic_hash == sample_header.extrinsic_hash
        assert deserialized_header.slot == sample_header.slot
        assert deserialized_header.author_index == sample_header.author_index
        assert deserialized_header.entropy_source == sample_header.entropy_source
        assert deserialized_header.seal == sample_header.seal

    def test_json_roundtrip(self, sample_header):
        """Test complete JSON roundtrip through string serialization."""
        # Convert to JSON string
        json_str = json.dumps(sample_header.to_json())
        
        # Parse JSON string back to dict
        parsed_json = json.loads(json_str)
        
        # Convert back to DemoHeader
        roundtrip_header = DemoHeader.from_json(parsed_json)
        
        # Verify all fields match
        assert roundtrip_header.parent == sample_header.parent
        assert roundtrip_header.parent_state_root == sample_header.parent_state_root
        assert roundtrip_header.extrinsic_hash == sample_header.extrinsic_hash
        assert roundtrip_header.slot == sample_header.slot
        assert roundtrip_header.author_index == sample_header.author_index
        assert roundtrip_header.entropy_source == sample_header.entropy_source
        assert roundtrip_header.seal == sample_header.seal

    def test_json_validation(self):
        """Test JSON validation and error handling."""
        # Test missing field
        invalid_json = {
            'parent': '0x' + '00' * 32,
            # missing parent_state_root
            'extrinsic_hash': '0x' + '22' * 32,
            'slot': 123,
            'author_index': 456,
            'entropy_source': '0x' + '55' * 32,
            'seal': '0x' + '66' * 32
        }
        with pytest.raises(ValueError, match="Missing field parent_state_root"):
            DemoHeader.from_json(invalid_json)

        # Test invalid hex string
        invalid_json = {
            'parent': 'invalid_hex',
            'parent_state_root': '0x' + '11' * 32,
            'extrinsic_hash': '0x' + '22' * 32,
            'slot': 123,
            'author_index': 456,
            'entropy_source': '0x' + '55' * 32,
            'seal': '0x' + '66' * 32
        }
        with pytest.raises(ValueError, match="Data must be a hex string starting with '0x'"):
            DemoHeader.from_json(invalid_json)

        # Test invalid type
        invalid_json = {
            'parent': '0x' + '00' * 32,
            'parent_state_root': '0x' + '11' * 32,
            'extrinsic_hash': '0x' + '22' * 32,
            'slot': "not_a_number",  # should be int
            'author_index': 456,
            'entropy_source': '0x' + '55' * 32,
            'seal': '0x' + '66' * 32
        }
        with pytest.raises(TypeError, match="Value must be an integer"):
            DemoHeader.from_json(invalid_json)
