"""Epoch-related protocol types for the JAM protocol."""
from dataclasses import dataclass
from typing import List, Any, Tuple, Optional, Sequence
from jam.types.protocol.validators import ValidatorArray
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import OpaqueHash

@dataclass
class EpochMark(Codable):
    """Epoch mark structure."""
    entropy: OpaqueHash
    tickets_entropy: OpaqueHash
    validators: ValidatorArray

    def enc_sequence(self) -> Sequence[Codable]:
        sequence = [self.entropy, self.tickets_entropy]
        sequence.extend(self.validators)
        return sequence

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
        entropy, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        tickets_entropy, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        validators, size = ValidatorArray.decode_from(buffer, current_offset)
        current_offset += size
        
        return EpochMark(entropy, tickets_entropy, validators), current_offset - offset
