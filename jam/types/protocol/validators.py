from dataclasses import dataclass
from typing import List, Any, Tuple, Sequence

from jam.types.base.array import Array
from jam.types.base.integers import U16, U32, U64
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import (
    BandersnatchPublic, Ed25519Public, BlsPublic
)
from jam.utils.codec.composite.arrays import ArrayCodec
from jam.utils.constants import VALIDATOR_COUNT

from jam.utils.constants import VALIDATOR_COUNT

class ValidatorArray(Array[BandersnatchPublic]):
    """Fixed-size array of validators."""
    def __init__(self, validators: List[BandersnatchPublic]):
        super().__init__(VALIDATOR_COUNT, validators)
    
    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        return ArrayCodec.decode_from(VALIDATOR_COUNT, BandersnatchPublic, buffer, offset)

@dataclass
class ValidatorMetadata(Codable):
    """Validator metadata structure."""
    data: bytes  # 128 bytes fixed size

    def encode_size(self) -> int:
        return 128

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        buffer[offset:offset + 128] = self.data
        return 128

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        return ValidatorMetadata(buffer[offset:offset + 128]), 128

@dataclass
class ValidatorData(Codable):
    """Validator data structure."""
    bandersnatch: BandersnatchPublic
    ed25519: Ed25519Public
    bls: BlsPublic
    metadata: ValidatorMetadata

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.bandersnatch, self.ed25519, self.bls, self.metadata]

    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        decoded = []
        for item_type in [BandersnatchPublic, Ed25519Public, BlsPublic, ValidatorMetadata]:
            item, size = item_type.decode_from(buffer, current_offset)
            decoded.append(item)
            current_offset += size
        return ValidatorData(*decoded), current_offset - offset

class ValidatorsData(Array[ValidatorData]):
    """Fixed-size array of validator data with size VALIDATOR_COUNT."""
    
    def __init__(self, items: List[ValidatorData]):
        super().__init__(VALIDATOR_COUNT, items)

    @classmethod
    def decode_from(cls, buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        return ArrayCodec.decode_from(VALIDATOR_COUNT, ValidatorData, buffer, offset) 
