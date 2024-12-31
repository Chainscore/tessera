from dataclasses import dataclass
from typing import List, Any, Tuple, Optional, Sequence
from jam.types.base.choice import Choice
from jam.types.base.array import Array
from jam.types.base.null import Null
from jam.types.base.vector import Vector
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import (
    HeaderHash, StateRoot, OpaqueHash
)
from jam.utils.codec.composite.arrays import ArrayCodec
from jam.utils.constants import RECENT_HISTORY_SIZE

class Mmr(Vector[Choice]):
    """Merkle Mountain Range structure."""
    def __init__(self, items: List[Choice]):
        super().__init__(items)

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        peaks = []
        current_offset = offset
        while current_offset < len(buffer):
            peak, size = Choice.decode_from([Null, OpaqueHash], buffer, current_offset)
            peaks.append(peak)
            current_offset += size
        return Mmr(peaks), current_offset - offset

@dataclass
class ReportedWorkPackage(Codable):
    """Reported work package structure."""
    hash: OpaqueHash
    exports_root: OpaqueHash

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.hash, self.exports_root]

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
        hash_val, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        exports_root, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        return ReportedWorkPackage(hash_val, exports_root), current_offset - offset

@dataclass
class BlockInfo(Codable):
    """Block information structure."""
    header_hash: HeaderHash
    mmr: Mmr
    state_root: StateRoot
    reported: List[ReportedWorkPackage]

    def enc_sequence(self) -> Sequence[Codable]:
        sequence = [self.header_hash, self.mmr, self.state_root]
        sequence.extend(self.reported)
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
        header_hash, size = HeaderHash.decode_from(buffer, current_offset)
        current_offset += size
        mmr, size = Mmr.decode_from(buffer, current_offset)
        current_offset += size
        state_root, size = StateRoot.decode_from(buffer, current_offset)
        current_offset += size
        
        reported = []
        while current_offset < len(buffer):
            report, size = ReportedWorkPackage.decode_from(buffer, current_offset)
            reported.append(report)
            current_offset += size
        
        return BlockInfo(header_hash, mmr, state_root, reported), current_offset - offset

class BlocksHistory(Array[BlockInfo]):
    """Fixed-size array of block information."""
    def __init__(self, blocks: List[BlockInfo]):
        super().__init__(RECENT_HISTORY_SIZE, blocks) 
    
    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        return ArrayCodec.decode_from(RECENT_HISTORY_SIZE, BlockInfo, buffer, offset)
