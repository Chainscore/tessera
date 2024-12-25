"""Assurance types for the JAM protocol."""
from dataclasses import dataclass
from typing import List
from .base import ByteSequence
from .core import OpaqueHash, ValidatorIndex
from .crypto import Ed25519Signature

@dataclass
class AvailAssurance:
    """Availability assurance structure."""
    anchor: OpaqueHash
    bitfield: ByteSequence  # Size should be avail_bitfield_bytes from constants
    validator_index: ValidatorIndex
    signature: Ed25519Signature

    def __post_init__(self):
        # avail_bitfield_bytes should be imported from constants
        if len(self.bitfield) != 0:  # avail_bitfield_bytes
            raise ValueError("Bitfield size does not match avail_bitfield_bytes")

@dataclass
class AssurancesExtrinsic:
    """Assurances extrinsic structure."""
    assurances: List[AvailAssurance]

    def __post_init__(self):
        # validators_count should be imported from constants
        if len(self.assurances) > 0:  # validators_count
            raise ValueError("AssurancesExtrinsic exceeds validators count") 