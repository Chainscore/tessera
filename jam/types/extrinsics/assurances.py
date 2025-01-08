from dataclasses import dataclass
from typing import Sequence
from jam.types.base import BitSequence, decodable_bit_sequence
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import Ed25519Signature, OpaqueHash
from jam.types.protocol.core import ValidatorIndex
from jam.utils.codec.base import Codable
from jam.utils.constants import CORE_COUNT

@decodable_bit_sequence(CORE_COUNT)
class AvailBitField(BitSequence): pass

@dataclass
class AvailAssurance(Codable):
    """Availability assurance structure."""
    anchor: OpaqueHash
    bitfield: AvailBitField
    validator_index: ValidatorIndex
    signature: Ed25519Signature

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.anchor, self.bitfield, self.validator_index, self.signature]
    
    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())
    
    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset
    
    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0):
        anchor, size = OpaqueHash.decode_from(buffer, offset)
        current_offset = offset + size
        bitfield, size = AvailBitField.decode_from(buffer, current_offset)
        current_offset += size
        validator_index, size = ValidatorIndex.decode_from(buffer, current_offset)
        current_offset += size
        signature, size = Ed25519Signature.decode_from(buffer, current_offset)
        current_offset += size
        return AvailAssurance(anchor, bitfield, validator_index, signature), current_offset - offset


@decodable_vector(AvailAssurance)
class AssurancesExtrinsic(Vector[AvailAssurance]): pass;