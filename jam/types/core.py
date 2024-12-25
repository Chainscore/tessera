"""Core types for the JAM protocol."""
from dataclasses import dataclass
from typing import List, NewType
from .base import ByteArray32, U16, U32, U64
from .crypto import BandersnatchPublic, Ed25519Public, BlsPublic

# Core type aliases
OpaqueHash = NewType('OpaqueHash', ByteArray32)
TimeSlot = NewType('TimeSlot', U32)
ValidatorIndex = NewType('ValidatorIndex', U16)
CoreIndex = NewType('CoreIndex', U16)

# Hash type aliases
HeaderHash = NewType('HeaderHash', OpaqueHash)
StateRoot = NewType('StateRoot', OpaqueHash)
BeefyRoot = NewType('BeefyRoot', OpaqueHash)
WorkPackageHash = NewType('WorkPackageHash', OpaqueHash)
WorkReportHash = NewType('WorkReportHash', OpaqueHash)
ExportsRoot = NewType('ExportsRoot', OpaqueHash)
ErasureRoot = NewType('ErasureRoot', OpaqueHash)

# Other core types
Gas = NewType('Gas', U64)
Entropy = NewType('Entropy', OpaqueHash)
ValidatorMetadata = NewType('ValidatorMetadata', bytes)

@dataclass
class ValidatorData:
    """Validator data structure."""
    bandersnatch: BandersnatchPublic
    ed25519: Ed25519Public
    bls: BlsPublic
    metadata: ValidatorMetadata

    @classmethod
    def validate(cls, value: bytes) -> 'ValidatorData':
        """Validate and create a ValidatorData value."""
        if len(value) != 128:
            raise ValueError(f"ValidatorMetadata must be exactly 128 bytes, got {len(value)}")
        return cls(
            bandersnatch=BandersnatchPublic(value[:32]),
            ed25519=Ed25519Public(value[32:64]),
            bls=BlsPublic(value[64:96]),
            metadata=ValidatorMetadata(value[96:])
        )

@dataclass
class EntropyBuffer:
    """Entropy buffer containing 4 entropy values."""
    values: List[Entropy]

    def __post_init__(self):
        if len(self.values) != 4:
            raise ValueError("EntropyBuffer must contain exactly 4 entropy values")

ServiceId = NewType('ServiceId', U32)

@dataclass
class ServiceInfo:
    """Service information structure."""
    code_hash: OpaqueHash
    balance: U64
    min_item_gas: Gas
    min_memo_gas: Gas
    bytes: U64
    items: U32 