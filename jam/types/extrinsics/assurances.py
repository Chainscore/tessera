
from dataclasses import dataclass
from typing import List, Self, Sequence, Tuple, Union
from jam.types.base.array import Array
from jam.types.base.bit_sequence import Bits
from jam.types.protocol.crypto import Ed25519Signature, OpaqueHash
from jam.types.protocol.core import ValidatorIndex
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.arrays import ArrayCodec
from jam.utils.codec.composite.bit_sequences import BitSequence
from jam.utils.constants import CORE_COUNT, VALIDATOR_COUNT

class AvailBitField(Bits):
    """Availability bitfield structure: octets of size VALIDATOR_COUNT"""
    def __init__(self, data: Sequence[BitSequence] = [False] * CORE_COUNT):
        super().__init__(data)
    
    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0):
        data, size = Bits.decode_from(CORE_COUNT, buffer, offset)
        return AvailBitField(data), size

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

class AssurancesExtrinsic(Array[AvailAssurance]):
    """Fixed-size array of availability assurances for an extrinsic."""
    def __init__(self, entries: List[AvailAssurance]):
        super().__init__(VALIDATOR_COUNT, entries)

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        entries, size = ArrayCodec.decode_from(VALIDATOR_COUNT, AvailAssurance, buffer, offset)
        return AssurancesExtrinsic(entries), size
