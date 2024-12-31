from dataclasses import dataclass
from typing import Any, Sequence, Tuple, Union
from jam.types.header import Header
from jam.utils.codec.base import Codable
from jam.types.extrinsics import (
    TicketsExtrinsic, PreimagesExtrinsic,
    GuaranteesExtrinsic, AssurancesExtrinsic,
    DisputesExtrinsic
)

@dataclass
class Extrinsic(Codable):
    """Extrinsic structure."""
    tickets: TicketsExtrinsic
    preimages: PreimagesExtrinsic
    guarantees: GuaranteesExtrinsic
    assurances: AssurancesExtrinsic
    disputes: DisputesExtrinsic

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.tickets, self.preimages, self.guarantees, self.assurances, self.disputes]
    
    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())
    
    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        tickets, size = TicketsExtrinsic.decode_from(buffer, offset)
        current_offset = offset + size
        preimages, size = PreimagesExtrinsic.decode_from(buffer, current_offset)
        current_offset += size
        guarantees, size = GuaranteesExtrinsic.decode_from(buffer, current_offset)
        current_offset += size
        assurances, size = AssurancesExtrinsic.decode_from(buffer, current_offset)
        current_offset += size
        disputes, size = DisputesExtrinsic.decode_from(buffer, current_offset)
        return Extrinsic(tickets, preimages, guarantees, assurances, disputes), current_offset - offset


@dataclass
class Block(Codable):
    """Block structure."""
    header: Header
    extrinsic: Extrinsic

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.header, self.extrinsic]

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
        header, size = Header.decode_from(buffer, offset)
        current_offset = offset + size
        extrinsic, size = Extrinsic.decode_from(buffer, current_offset)
        return Block(header, extrinsic), current_offset - offset